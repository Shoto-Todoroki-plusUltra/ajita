"""Bounded exhaustive mathematical certificate, not a sampler/benchmark runner."""

import hashlib
import json
import math
import time
from itertools import product
from pathlib import Path

from quantum_workload_studio.classical.timetable import cp_sat_solve, enumerate_solve
from quantum_workload_studio.classical.tsp import exact_solve
from quantum_workload_studio.execution.research_mapping import (
    B1ResearchInput,
    TspResearchInput,
    artifact_digest,
    prepare_b1,
    prepare_tsp,
)
from quantum_workload_studio.models.timetable import (
    Placement,
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.models.tsp import TspInstance, evaluate_original_objective
from quantum_workload_studio.qubo.timetable import compile_qubo as compile_b1
from quantum_workload_studio.qubo.timetable import decode, direct_energy
from quantum_workload_studio.qubo.tsp import compile_qubo as compile_tsp
from quantum_workload_studio.qubo.tsp import decode_assignment, direct_evaluate

POLICIES = {
    "T0": [4, 16, 64],
    "T1": [14, 56, 224],
    "B0": [1, 6, 24],
    "B1": [2, 10, 40],
    "N0": [1, 4],
    "N1": [1],
}
EXPECTED = {
    "T0": (9, 6, 4, 2),
    "T1": (9, 6, 10, 2),
    "B0": (4, 2, 1, 1),
    "B1": (8, 8, 1, 1),
    "N0": (2, 0, None, 0),
    "N1": (0, 0, None, 0),
}


def original_reference(instance):
    """Enumerate original assignments without consulting any QUBO mapping."""
    if isinstance(instance, TspInstance):
        oracle = exact_solve(instance)
        costs = [r.objective for r in oracle.enumerated_routes]
        return oracle.model_dump(), costs
    oracle = enumerate_solve(instance)
    native = cp_sat_solve(instance, timeout_s=10.0, seed=1729)
    if oracle.objective != native.objective or oracle.proven_infeasible != native.proven_infeasible:
        raise ValueError("original enumerator and native CP-SAT disagree; mapping gate blocked")
    choices = [(r.id, s.id) for r in instance.rooms for s in instance.slots]
    costs = []
    for selected in product(choices, repeat=len(instance.courses)):
        candidate = TimetableAssignment(
            assignments=[
                Placement(course_id=c.id, room_id=r, slot_id=s)
                for c, (r, s) in zip(instance.courses, selected)
            ]
        )
        if validate_assignment(instance, candidate).feasible:
            costs.append(original_objective(instance, candidate))
    return {"enumeration": oracle.model_dump(), "cp_sat": native.model_dump()}, costs


def certify_fixtures(root: Path):
    from qiskit.quantum_info import Statevector

    start, outputs = time.monotonic(), []
    for name, penalties in POLICIES.items():
        path = root / "examples/research_mapping" / f"{name}.json"
        data = json.loads(path.read_text())
        instance = (TspInstance if data["kind"] == "tsp" else TimetableInstance).model_validate(
            data
        )
        reference, costs = original_reference(instance)
        q_expected, feasible_expected, optimum_expected, opt_count_expected = EXPECTED[name]
        if (
            len(costs) != feasible_expected
            or (min(costs) if costs else None) != optimum_expected
            or costs.count(optimum_expected) != opt_count_expected
        ):
            raise ValueError(
                f"frozen original reference discrepancy for {name}; owner review required"
            )
        for penalty in penalties:
            if time.monotonic() - start > 120:
                raise TimeoutError("mathematical certificate 120s budget exceeded")
            tsp = isinstance(instance, TspInstance)
            artifact = (compile_tsp if tsp else compile_b1)(instance, penalty=penalty)
            if len(artifact.variables) != q_expected:
                raise ValueError(f"frozen variable count discrepancy for {name}")
            request_type, prepare = (
                (TspResearchInput, prepare_tsp) if tsp else (B1ResearchInput, prepare_b1)
            )
            raw_request = request_type(
                schema_version=1,
                artifact=artifact,
                artifact_sha256=artifact_digest(artifact),
                normalization="none",
            )
            artifact, raw_mapping = prepare(instance, raw_request)
            normalized_request = (
                raw_request.model_copy(update={"normalization": "ising_l1"}) if q_expected else None
            )
            normalized_mapping = prepare(instance, normalized_request)[1] if q_expected else None
            operator, offset = (
                raw_mapping.sparse_operator() if q_expected else (None, raw_mapping.basis.offset)
            )
            normalized_operator, normalized_offset = (
                normalized_mapping.sparse_operator() if q_expected else (None, None)
            )
            rows = []
            for integer in range(2**q_expected):
                if time.monotonic() - start > 120:
                    raise TimeoutError("mathematical certificate 120s budget exceeded")
                bits = [(integer >> i) & 1 for i in range(q_expected)]
                direct = (
                    direct_evaluate(instance, bits, penalty).energy
                    if tsp
                    else direct_energy(instance, artifact, bits)
                )
                expanded, ising = artifact.energy(bits), raw_mapping.basis.energy(bits)
                if expanded != direct or ising != direct:
                    raise ValueError(
                        f"exact direct/expanded/Ising mismatch for {name}/{penalty}/{integer}"
                    )
                state = Statevector.from_int(integer, 2**q_expected) if q_expected else None
                total = (
                    complex(state.expectation_value(operator)) + offset
                    if state is not None
                    else complex(ising)
                )
                norm = (
                    complex(state.expectation_value(normalized_operator)) + normalized_offset
                    if state is not None
                    else None
                )
                for value, expected in [
                    (total, direct),
                    *(([(norm, direct / normalized_mapping.divisor)]) if norm is not None else []),
                ]:
                    if abs(value.imag) > 1e-10 or not math.isclose(
                        value.real, expected, rel_tol=1e-12, abs_tol=1e-10
                    ):
                        raise ValueError(
                            f"SDK basis parity mismatch for {name}/{penalty}/{integer}"
                        )
                outcome = (
                    decode_assignment(instance, bits) if tsp else decode(instance, artifact, bits)
                )
                original = (
                    (
                        evaluate_original_objective(instance, outcome.assignment)
                        if tsp
                        else outcome.original_objective
                    )
                    if outcome.validation.feasible
                    else None
                )
                rows.append(
                    {
                        "integer": integer,
                        "bits_index_order": bits,
                        "direct_energy": direct,
                        "expanded_energy": expanded,
                        "classical_ising_energy": ising,
                        "sdk_total_energy": total.real if state is not None else None,
                        "normalized_sdk_total_energy": norm.real if norm is not None else None,
                        "absolute_error": abs(total.real - direct),
                        "normalized_absolute_error": abs(
                            norm.real - direct / normalized_mapping.divisor
                        )
                        if norm is not None
                        else None,
                        "validation": outcome.validation.model_dump(),
                        "original_objective": original,
                    }
                )
            feasible_rows = [r for r in rows if r["validation"]["feasible"]]
            if len(feasible_rows) != len(costs) or sorted(
                r["original_objective"] for r in feasible_rows
            ) != sorted(costs):
                raise ValueError("decoded bitspace differs from independent original enumeration")
            ground = min(r["direct_energy"] for r in rows)
            minima = [r for r in rows if r["direct_energy"] == ground]
            outputs.append(
                {
                    "fixture": name,
                    "penalty": penalty,
                    "instance": instance.model_dump(),
                    "fixture_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "reference": reference,
                    "original_feasible_costs": costs,
                    "qubo": artifact.model_dump(),
                    "mapping": raw_mapping.metadata(),
                    "normalized_mapping": normalized_mapping.metadata()
                    if normalized_mapping
                    else None,
                    "operator_terms": [[p, float(c.real)] for p, c in operator.to_list()]
                    if operator is not None
                    else None,
                    "sdk_status": "all_basis_expectations_checked"
                    if q_expected
                    else "constant_only_no_zero_qubit_sdk_claim",
                    "feasible_assignments": len(costs),
                    "optimum": optimum_expected,
                    "minimum_infeasible_energy": min(
                        (r["direct_energy"] for r in rows if not r["validation"]["feasible"]),
                        default=None,
                    ),
                    "all_ground_states_feasible": all(r["validation"]["feasible"] for r in minima),
                    "ground_state_count": len(minima),
                    "ground_energy": ground,
                    "basis_states": rows,
                    "max_absolute_error": max(r["absolute_error"] for r in rows),
                    "absolute_tolerance": 1e-10,
                    "relative_tolerance": 1e-12,
                }
            )
    if sum(len(c["basis_states"]) for c in outputs) != 3897:
        raise ValueError("protocol basis-row count mismatch")
    return {
        "kind": "mathematical_mapping_certificate; not study or sampler data",
        "certificates": outputs,
        "basis_rows": 3897,
        "sampler_calls": 0,
        "elapsed_s": time.monotonic() - start,
    }


def certificate_worker(send, payload):
    try:
        from qiskit.primitives import StatevectorSampler

        from quantum_workload_studio.execution import local

        def denied(*args, **kwargs):
            raise RuntimeError("mapping certificate forbids sampler/QAOA execution")

        StatevectorSampler.run = denied
        local._qaoa_worker = denied
        send.send({"kind": "completed", "certificate": certify_fixtures(Path(payload["root"]))})
    except BaseException as exc:
        send.send({"kind": "error", "type": type(exc).__name__, "message": str(exc)})
    finally:
        send.close()
