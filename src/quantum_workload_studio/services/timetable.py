"""Classical B1 service, usable without any quantum dependency."""

import time

from quantum_workload_studio.classical.timetable import cp_sat_solve, enumerate_solve
from quantum_workload_studio.models.timetable import TimetableInstance


def solve_classical(instance, solver="cp_sat", *, timeout_s=10.0, seed=1729):
    if solver == "cp_sat":
        return cp_sat_solve(instance, timeout_s=timeout_s, seed=seed)
    if solver == "enumeration":
        return enumerate_solve(instance)
    raise ValueError("unsupported B1 solver")


def classical_worker(send, payload):
    start = time.monotonic()
    try:
        send.send({"kind": "worker_entry"})
        before = time.monotonic()
        send.send({"kind": "import_started"})
        if payload["solver"] == "cp_sat":
            from ortools.sat.python import cp_model  # noqa: F401
        imports = time.monotonic() - before if payload["solver"] == "cp_sat" else None
        send.send({"kind": "imports_complete", "import_s": imports})
        answer = solve_classical(
            TimetableInstance.model_validate(payload["instance"]),
            payload["solver"],
            timeout_s=payload["timeout_s"],
            seed=payload["seed"],
        )
        send.send(
            {
                "kind": "completed",
                "result": answer.model_dump(),
                "worker_timings": {
                    "ortools_import_s": imports,
                    "model_and_solver_s": answer.solver_elapsed_s,
                    "worker_entry_to_result_s": time.monotonic() - start,
                },
            }
        )
    except BaseException as exc:
        send.send({"kind": "error", "type": type(exc).__name__, "message": str(exc)})
    finally:
        send.close()
