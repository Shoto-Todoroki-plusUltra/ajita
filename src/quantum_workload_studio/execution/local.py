"""Bounded local QAOA experiment in a killable spawned worker.

No classical fallback. Parent retains streamed samples even after a timeout/error.
RSS is sampled enforcement, NOT a kernel hard memory reservation/ceiling.
"""
import math
import multiprocessing as mp
import os
import threading
import time
from typing import Annotated, Literal

from pydantic import Field, model_validator

from quantum_workload_studio.models.tsp import StrictModel, TspInstance, evaluate_original_objective
from quantum_workload_studio.qubo.tsp import bits_from_display, compile_qubo, decode_assignment
from quantum_workload_studio.execution.operator import normalize_counts


class LocalOptions(StrictModel):
    backend: Literal["statevector", "aer"] = "statevector"
    seed: Annotated[int, Field(ge=0, le=2**31-1)] = 1729
    transpiler_seed: Annotated[int, Field(ge=0, le=2**31-1)] = 7
    shots: Annotated[int, Field(ge=1, le=4096)] = 256
    reps: Annotated[int, Field(ge=1, le=2)] = 1
    max_evaluations: Annotated[int, Field(ge=4, le=50)] = 16
    timeout_s: Annotated[float, Field(gt=0, le=60, allow_inf_nan=False)] = 60.0
    memory_limit_mb: Annotated[int, Field(ge=64, le=4096)] = 1024
    optimization_level: Annotated[int, Field(ge=0, le=3)] = 1

    @model_validator(mode="after")
    def optimizer_budget(self):
        if self.max_evaluations < 2*self.reps+2:
            raise ValueError("COBYLA requires at least 2*reps+2 evaluations")
        return self


def memory_preflight(variable_count, options, *, available_bytes=None):
    """Refuse before spawning/allocating. Estimates are deliberately labeled."""
    import psutil

    if type(variable_count) is not int or not 1 <= variable_count <= 16:
        raise ValueError("local statevector mode limited to 16 active variables")
    amplitude_bytes = 16*2**variable_count
    # Modeled workspace factor and import allowance; not measured peak memory.
    modeled = 8*amplitude_bytes+256*1024**2
    limit = options.memory_limit_mb*1024**2
    available = psutil.virtual_memory().available if available_bytes is None else available_bytes
    if modeled > limit:
        raise ValueError("modeled workspace/import allowance exceeds memory budget")
    if limit > available//2:
        raise ValueError("memory budget exceeds half currently available system RAM")
    return {"amplitude_lower_bound_bytes": amplitude_bytes, "modeled_allowance_bytes": modeled,
            "available_bytes_observed": available, "rss_limit_bytes": limit,
            "enforcement": "10ms polling wait plus per-event validation and OS scheduling; may overshoot, not a kernel hard cap"}


def summarize_samples(instance, counts):
    """Count-weighted original feasibility; malformed keys remain invalid shots."""
    n = (len(instance.city_ids)-1)**2
    rows, feasible, invalid = [], 0, 0
    best = None
    for displayed, count in sorted(counts.items()):
        if type(count) is not int or count <= 0:
            raise ValueError("raw shot counts must be positive integers")
        try:
            bits = bits_from_display(displayed, n)
            decoded = decode_assignment(instance, bits)
            objective = evaluate_original_objective(instance, decoded.assignment) if decoded.assignment else None
            row = {"display": displayed, "count": count, "bits": bits,
                   **decoded.model_dump(), "original_objective": objective}
        except ValueError as error:
            row = {"display": displayed, "count": count, "bits": None, "assignment": None,
                   "validation": {"checked": True, "feasible": False,
                                  "violations": [{"code": "malformed_sample", "message": str(error)}]},
                   "original_objective": None}
            objective = None
        if objective is None:
            invalid += count
        else:
            feasible += count
            if best is None or objective < best["original_objective"]:
                best = row
        rows.append(row)
    total = feasible+invalid
    return {"raw_counts": counts, "raw_shots": total, "feasible_shots": feasible, "invalid_shots": invalid,
            "feasible_fraction": feasible/total if total else None,
            "invalid_fraction": invalid/total if total else None,
            "candidate_outcome": "feasible" if best else "no_feasible_sample",
            "best_feasible": best, "decoded_unique_samples": rows}


def _qaoa_worker(send, payload):
    """Only genuine sampler output may enter a sample event."""
    try:
        # Set before numerical/SDK imports inside the fresh interpreter.
        for name in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "RAYON_NUM_THREADS"]:
            os.environ[name] = "1"
        import numpy as np
        from scipy.optimize import minimize
        from qiskit import transpile
        from qiskit.circuit.library import qaoa_ansatz
        from qiskit.primitives import StatevectorSampler
        from quantum_workload_studio.execution.operator import sparse_operator

        start = time.monotonic()
        instance = TspInstance.model_validate(payload["instance"])
        options = LocalOptions.model_validate(payload["options"])
        qubo = compile_qubo(instance)
        operator, offset = sparse_operator(qubo)
        # No offset in evolution: global phase only. Sample objective includes it.
        circuit = qaoa_ansatz(operator, reps=options.reps, flatten=True)
        pre = {"depth": circuit.depth(), "gates": dict(circuit.count_ops()), "qubits": circuit.num_qubits}
        circuit.measure_all()
        trans_start = time.monotonic()
        compiled = transpile(circuit, basis_gates=["u", "cx"], seed_transpiler=options.transpiler_seed,
                             optimization_level=options.optimization_level)
        post = {"depth": compiled.depth(), "gates": dict(compiled.count_ops()), "qubits": compiled.num_qubits,
                "two_qubit_gates": sum(1 for instruction in compiled.data if instruction.operation.num_qubits == 2)}
        parameter_order = list(compiled.parameters)
        rng = np.random.default_rng(options.seed)
        initial = rng.uniform(0, 2*np.pi, size=len(parameter_order))
        initial_values = {str(p): float(x) for p, x in zip(parameter_order, initial)}
        send.send({"kind": "circuit", "pre": pre, "post": post, "parameter_order": [str(p) for p in parameter_order],
                   "initial_values": initial_values, "identity_offset": offset,
                   "transpile_seconds": time.monotonic()-trans_start,
                   "target": "local all-to-all u/cx basis; no device calibration or hardware model",
                   "logical_to_classical": list(range(circuit.num_qubits))})
        evaluations = 0

        def objective(parameters):
            nonlocal evaluations
            if evaluations >= options.max_evaluations:
                raise RuntimeError("evaluation guard reached (optimizer exceeded requested budget)")
            sample_seed = options.seed+evaluations
            if options.backend == "statevector":
                sampler = StatevectorSampler(seed=sample_seed)
            else:
                from qiskit_aer.primitives import SamplerV2
                sampler = SamplerV2(seed=sample_seed, options={"backend_options": {
                    "method": "statevector", "max_parallel_threads": 1, "max_parallel_experiments": 1,
                    "max_parallel_shots": 1, "max_memory_mb": options.memory_limit_mb}})
            # Bind by Parameter objects in the recorded compiled order, never guess beta/gamma order.
            bound = compiled.assign_parameters(dict(zip(parameter_order, parameters)))
            raw = sampler.run([bound], shots=options.shots).result()[0].data.meas.get_counts()
            # Stream immediately so all received samples survive later errors/cancellation.
            send.send({"kind": "samples", "evaluation": evaluations, "seed": sample_seed,
                       "parameters": [float(v) for v in parameters], "raw_counts": raw,
                       "logical_to_classical": list(range(circuit.num_qubits))})
            normalized = normalize_counts(raw, list(range(circuit.num_qubits)))
            if sum(raw.values()) != options.shots:
                raise RuntimeError("sampler returned a different shot count")
            mean = math.fsum(qubo.energy(bits_from_display(s, len(qubo.variables)))*count
                             for s, count in normalized.items())/options.shots
            evaluations += 1
            return mean

        solve_start = time.monotonic()
        optimized = minimize(objective, initial, method="COBYLA",
                             options={"maxiter": options.max_evaluations, "rhobeg": 0.5, "tol": 1e-3})
        send.send({"kind": "completed", "optimizer": {"name": "SciPy COBYLA", "nfev": int(optimized.nfev),
                   "success": bool(optimized.success), "message": str(optimized.message),
                   "fun_penalized_sample_mean": float(optimized.fun), "parameters": optimized.x.tolist()},
                   "solve_seconds": time.monotonic()-solve_start, "worker_seconds_after_import": time.monotonic()-start})
    except BaseException as error:
        send.send({"kind": "error", "type": type(error).__name__, "message": str(error)})
    finally:
        send.close()


def supervise(payload, options, *, cancel=None, target=None, on_event=None):
    """Parent deadline includes spawn/import/compile/solve. Cleanup grace is separate.

    target is dependency injection for lifecycle tests only, never a solver fallback.
    """
    import psutil

    started = time.monotonic()
    context = mp.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    worker = context.Process(target=target or _qaoa_worker, args=(send, payload))
    events, peak, status, monitor_error = [], 0, None, None
    previous_check, max_check_interval = None, 0.0
    spawn_start = time.monotonic()
    worker.start()
    process_start_call_s = time.monotonic()-spawn_start
    first_worker_event_s = None
    send.close()
    try:
        process = psutil.Process(worker.pid)
        while True:
            checked_at = time.monotonic()
            if previous_check is not None:
                max_check_interval = max(max_check_interval, checked_at-previous_check)
            previous_check = checked_at
            # Check the deadline/cancellation even if a worker floods the pipe.
            if time.monotonic()-started >= options.timeout_s:
                status = "timeout"
                break
            if cancel is not None and cancel.is_set():
                status = "cancelled"
                break
            try:
                rss = process.memory_info().rss
                peak = max(peak, rss)
                if rss > options.memory_limit_mb*1024**2:
                    status = "memory_limit"
                    break
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied as error:
                monitor_error = str(error)
                status = "monitor_unavailable"
                break  # fail closed; never claim enforcement we cannot observe
            if receive.poll(0.01):
                try:
                    event = receive.recv()
                except EOFError:
                    break
                events.append(event)
                if first_worker_event_s is None:
                    first_worker_event_s = time.monotonic()-started
                if on_event is not None:
                    try:
                        on_event(event)  # original validation is inside the supervised deadline
                    except (ValueError, TypeError) as error:
                        events.append({"kind": "error", "type": type(error).__name__, "message": str(error),
                                       "phase": "parent_sample_validation"})
                        status = "validation_error"
                        break  # raw event retained; fail closed and clean up
                if event["kind"] in ("completed", "error"):
                    status = "completed" if event["kind"] == "completed" else "error"
                    break
            if not worker.is_alive() and not receive.poll():
                break
    finally:
        compute_elapsed = time.monotonic()-started
        cleanup_start = time.monotonic()
        forced_cleanup = False
        # A completed message does not excuse a worker which remains alive.
        if status != "completed" and worker.is_alive():
            forced_cleanup = True
            worker.terminate()
        worker.join(timeout=0.25)
        if worker.is_alive():
            forced_cleanup = True
            worker.kill()
            worker.join(timeout=0.75)
        alive = worker.is_alive()
        exitcode, pid = worker.exitcode, worker.pid
        receive.close()
        if not alive:
            worker.close()
        cleanup_elapsed = time.monotonic()-cleanup_start
    if alive:
        status = "cleanup_failed"
    elif status == "completed" and (forced_cleanup or exitcode != 0):
        status = "unclean_worker_exit"
    return {"execution_status": status or "worker_failed", "events": events,
            "process_start_call_s": process_start_call_s,
            "first_worker_event_elapsed_s": first_worker_event_s,
            "observed_peak_worker_rss_bytes": peak or None,
            "monitor_error": monitor_error, "worker_pid": pid, "worker_exitcode": exitcode,
            "max_observed_watchdog_interval_s": max_check_interval,
            "worker_alive_after_cleanup": alive, "forced_cleanup": forced_cleanup, "compute_elapsed_s": compute_elapsed,
            "cleanup_elapsed_s": cleanup_elapsed, "supervisor_elapsed_s": time.monotonic()-started}


def run_local(instance, options=None, *, cancel=None):
    """Entry point: classical oracle is reference-only, never supplies candidates."""
    started = time.monotonic()
    options = options or LocalOptions()
    # Revalidate copies so mutable input lists cannot bypass preflight validation.
    instance = TspInstance.model_validate(instance.model_dump())
    options = LocalOptions.model_validate(options.model_dump())
    count = (len(instance.city_ids)-1)**2
    preflight = memory_preflight(count, options)
    from quantum_workload_studio.classical.tsp import exact_solve
    oracle_start = time.monotonic()
    oracle = exact_solve(instance)
    reference_seconds = time.monotonic()-oracle_start
    counts, sample_evaluations, decoded_rows, failures = {}, [], {}, []

    def on_event(event):
        if event["kind"] == "samples":
            normalized = normalize_counts(event["raw_counts"], event["logical_to_classical"])
            validated = summarize_samples(instance, normalized)
            sample_evaluations.append({**event, "validation": validated})
            for row in validated["decoded_unique_samples"]:
                key = row["display"]
                counts[key] = counts.get(key, 0)+row["count"]
                decoded_rows[key] = {**row, "count": counts[key]}
        elif event["kind"] == "error":
            failures.append(event)

    remaining = options.timeout_s-(time.monotonic()-started)
    if remaining <= 0:
        raise TimeoutError("deadline expired during preflight")
    worker_options = options.model_copy(update={"timeout_s": remaining})
    result = supervise({"instance": instance.model_dump(), "options": options.model_dump()}, worker_options,
                       cancel=cancel, on_event=on_event)
    failures = [event for event in result["events"] if event["kind"] == "error"]
    # No second decode outside the deadline; aggregate only already validated rows.
    rows = [decoded_rows[key] for key in sorted(decoded_rows)]
    feasible = sum(row["count"] for row in rows if row["validation"]["feasible"])
    total = sum(counts.values())
    best = min((row for row in rows if row["validation"]["feasible"]),
               key=lambda row: row["original_objective"], default=None)
    samples = {"raw_counts": counts, "raw_shots": total, "feasible_shots": feasible,
               "invalid_shots": total-feasible, "feasible_fraction": feasible/total if total else None,
               "invalid_fraction": (total-feasible)/total if total else None,
               "candidate_outcome": "feasible" if best else "no_feasible_sample",
               "best_feasible": best, "decoded_unique_samples": rows}
    best = samples["best_feasible"]
    gap = best["original_objective"]-oracle.objective if best else None
    elapsed = time.monotonic()-started
    if elapsed-result["cleanup_elapsed_s"] > options.timeout_s and result["execution_status"] == "completed":
        result["execution_status"] = "timeout"  # includes parent reference/validation, never relabel late completion
    return {"schema_version": 1, "method": "quantum_local", "backend": options.backend,
            "candidate_source": "V2 sampler shots only; no classical fallback or repair",
            "instance_hash": instance.instance_hash(), "options": options.model_dump(),
            "preflight": preflight, **result, "sample_evaluations": sample_evaluations,
            "samples": samples, "failures": failures,
            "selection_policy": "best verified feasible objective across all optimization shots; no repair, fallback or separate final-parameter quality claim",
            "reference": {"solver": "independent exact_tsp", "objective": oracle.objective,
                          "seconds": reference_seconds},
            "absolute_optimality_gap": gap,
            "relative_optimality_gap": (gap/oracle.objective if oracle.objective else (0.0 if gap == 0 else None)) if best else None,
            "total_elapsed_including_post_validation_s": elapsed,
            "deadline_scope": "preflight/reference plus spawn/import/compile/solve and parent validation; cleanup grace <=1s separately reported; scheduling/poll overshoot possible",
            "no_practical_quantum_speedup_demonstrated": True}
