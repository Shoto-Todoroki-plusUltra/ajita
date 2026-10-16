"""Classical CLI/API dispatch and killable process adapter."""

import os

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
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = "1"
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
        send.send({"kind": "completed", "result": data})
    except BaseException as error:
        send.send({"kind": "error", "type": type(error).__name__, "message": str(error)})
    finally:
        send.close()
