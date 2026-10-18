"""B1 contracts and routes. Shares admission/worker protections, not a universal IR."""

import time
from typing import Annotated, Literal

from fastapi import Request
from pydantic import Field

from quantum_workload_studio.classical.timetable import TimetableResult
from quantum_workload_studio.execution.local import LocalOptions, supervise
from quantum_workload_studio.models.timetable import (
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.models.tsp import StrictModel, ValidationReport
from quantum_workload_studio.qubo.timetable import (
    Decoded,
    TimetableQubo,
    compile_qubo,
    decode,
    verify_artifact,
)
from quantum_workload_studio.services.timetable import classical_worker
from quantum_workload_studio.timetable_cli import parse_bits


class Solve(StrictModel):
    method: Literal["classical"] = "classical"
    instance: TimetableInstance
    solver: Literal["cp_sat", "enumeration"] = "cp_sat"
    timeout_s: Annotated[float, Field(gt=0, le=60, allow_inf_nan=False)] = 10.0
    memory_limit_mb: Annotated[int, Field(ge=64, le=1024)] = 512
    seed: Annotated[int, Field(ge=0, lt=2**31)] = 1729


class Result(StrictModel):
    execution_status: Literal["completed"] = "completed"
    result: TimetableResult
    backend_computation_elapsed_s: float
    worker: dict


class Compile(StrictModel):
    instance: TimetableInstance
    penalty: Annotated[int, Field(ge=1, le=50_000_001)] | None = None
    scale: Annotated[float, Field(gt=0, le=1_000_000, allow_inf_nan=False)] = 1.0


class Inspect(StrictModel):
    instance: TimetableInstance
    qubo: TimetableQubo
    bits: Annotated[str, Field(max_length=16, pattern=r"^[01]*$")]


class Inspection(Decoded):
    energy: float


class Validate(StrictModel):
    instance: TimetableInstance
    assignment: TimetableAssignment


class Validation(StrictModel):
    validation: ValidationReport
    original_objective: int | None


def register(app, bounded, error):
    @app.post("/api/problems/timetable/solve", response_model=Result)
    async def solve(data: Solve, request: Request):
        # Preflight enumeration size before admitting the worker.
        n = (len(data.instance.rooms) * len(data.instance.slots)) ** len(data.instance.courses)
        if data.solver == "enumeration" and n > 65_536:
            return error("unsupported_size", "Enumeration supports at most 65536 assignments", 400)

        def compute(cancel):
            start = time.monotonic()
            try:
                raw = supervise(
                    {
                        "instance": data.instance.model_dump(),
                        "solver": data.solver,
                        "timeout_s": data.timeout_s,
                        "seed": data.seed,
                    },
                    LocalOptions(timeout_s=data.timeout_s, memory_limit_mb=data.memory_limit_mb),
                    cancel=cancel,
                    target=classical_worker,
                )
                app.state.last_worker = {
                    k: raw[k]
                    for k in [
                        "worker_pid",
                        "worker_exitcode",
                        "worker_alive_after_cleanup",
                        "forced_cleanup",
                    ]
                }
                if raw["execution_status"] != "completed":
                    return error(
                        raw["execution_status"],
                        "B1 worker did not finish cleanly",
                        504 if raw["execution_status"] == "timeout" else 503,
                        [raw],
                    )
                completed = next(e for e in raw["events"] if e["kind"] == "completed")
                return Result(
                    result=TimetableResult.model_validate(completed["result"]),
                    backend_computation_elapsed_s=time.monotonic() - start,
                    worker={
                        **{k: v for k, v in raw.items() if k != "events"},
                        "stage_timings": completed["worker_timings"],
                    },
                )
            except ImportError:
                return error("unsupported", "OR-Tools is unavailable", 400)
            except (ValueError, OverflowError) as exc:
                return error("resource_limit", str(exc), 400)
            except Exception:
                return error("execution_error", "B1 execution failed; no fallback used", 503)

        return await bounded(request, compute)

    @app.post("/api/problems/timetable/compile", response_model=TimetableQubo)
    async def compile(data: Compile):
        try:
            return compile_qubo(data.instance, penalty=data.penalty, scale=data.scale)
        except (ValueError, OverflowError) as exc:
            return error("unsupported_size", str(exc), 400)

    @app.post("/api/problems/timetable/inspect", response_model=Inspection)
    async def inspect(data: Inspect):
        try:
            verify_artifact(data.instance, data.qubo)
            bits = parse_bits(data.bits, len(data.qubo.variables))
            return Inspection(
                energy=data.qubo.energy(bits), **decode(data.instance, data.qubo, bits).model_dump()
            )
        except (ValueError, OverflowError) as exc:
            return error("invalid_qubo", str(exc), 422)

    @app.post("/api/problems/timetable/validate", response_model=Validation)
    async def validate(data: Validate):
        report = validate_assignment(data.instance, data.assignment)
        return Validation(
            validation=report,
            original_objective=original_objective(data.instance, data.assignment)
            if report.feasible
            else None,
        )
