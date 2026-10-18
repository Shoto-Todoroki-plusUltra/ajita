"""Classical CLI/API dispatch and killable process adapter."""

import os
import time

from quantum_workload_studio.classical.tsp import exact_solve, ortools_solve
from quantum_workload_studio.models.tsp import TspInstance


def solve_classical(instance, solver, *, scale=1000, timeout_s=1.0):
    if solver == "exact_tsp":
        return exact_solve(instance)
    if solver == "ortools_tsp":
        return ortools_solve(instance, scale=scale, timeout_s=timeout_s)
    raise ValueError("unsupported classical solver")


def classical_worker(send, payload):
    try:
        entered = time.monotonic()
        send.send({"kind": "worker_entry", "monotonic_s": entered})
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = "1"
        import_start = time.monotonic()
        send.send({"kind": "import_started", "monotonic_s": import_start})
        if payload["solver"] == "ortools_tsp":
            # Measure the same lazy imports performed by the original adapter.
            # No initialization/solver option is substituted as a warmup.
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2  # noqa: F401
        import_seconds = time.monotonic() - import_start
        send.send({"kind": "imports_complete", "import_seconds": import_seconds})
        dispatch_start = time.monotonic()
        result = solve_classical(
            TspInstance.model_validate(payload["instance"]),
            payload["solver"],
            scale=payload["scale"],
            timeout_s=payload["timeout_s"],
        )
        data = result.model_dump()
        # Full permutation tables belong in mathematical evidence, not HTTP responses.
        data.pop("enumerated_routes")
        data.pop("tied_optima")
        send.send(
            {
                "kind": "completed",
                "result": data,
                "worker_timings": {
                    "ortools_import_s": import_seconds
                    if payload["solver"] == "ortools_tsp"
                    else None,
                    "dispatch_validation_model_solver_s": time.monotonic() - dispatch_start,
                    "native_solver_s": result.solve_seconds
                    if payload["solver"] == "ortools_tsp"
                    else None,
                    "worker_entry_to_result_s": time.monotonic() - entered,
                },
            }
        )
    except BaseException as error:
        send.send({"kind": "error", "type": type(error).__name__, "message": str(error)})
    finally:
        send.close()
