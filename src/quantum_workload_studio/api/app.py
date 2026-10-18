"""Single-process loopback API. One active CPU job; excess work is rejected."""

import asyncio
import importlib.util
import json
import os
import threading
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from quantum_workload_studio.api.models import (
    ApiResult,
    CompileRequest,
    ErrorResponse,
    InspectRequest,
    InspectResult,
    QuantumSummary,
    SolveRequest,
)
from quantum_workload_studio.execution.local import LocalOptions, run_local, supervise
from quantum_workload_studio.models.tsp import ValidationReport, evaluate_original_objective
from quantum_workload_studio.qubo.tsp import (
    QuboArtifact,
    bits_from_display,
    compile_qubo,
    decode_assignment,
    verify_artifact,
)
from quantum_workload_studio.services.tsp import classical_worker

MAX_BODY = 2 * 1024**2
MAX_API_SHOTS = 8192  # bounds retained/decoded HTTP trace work in the parent too
ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173"}


def error(code, message, status=400, details=None):
    return JSONResponse(
        {"error": {"code": code, "message": message, "details": details or []}}, status_code=status
    )


class BoundedBody:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode()
        if origin and origin not in ORIGINS:
            return await error(
                "origin_rejected", "Only the local frontend origin is accepted", 403
            )(scope, receive, send)
        if headers.get(b"content-type", b"").split(b";")[0] != b"application/json":
            return await error("invalid_content_type", "Use application/json", 415)(
                scope, receive, send
            )
        chunks, size = [], 0
        try:
            async with asyncio.timeout(5):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    size += len(message.get("body", b""))
                    if size > MAX_BODY:
                        return await error("payload_limit", "JSON body exceeds 2 MiB", 413)(
                            scope, receive, send
                        )
                    chunks.append(message.get("body", b""))
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await error("body_timeout", "Request body deadline exceeded", 408)(
                scope, receive, send
            )
        body = b"".join(chunks)

        # Reject duplicate keys/nonfinite tokens instead of allowing parser-dependent semantics.
        def unique(pairs):
            data = {}
            for key, value in pairs:
                if key in data:
                    raise ValueError("duplicate JSON key")
                data[key] = value
            return data

        try:
            json.loads(
                body,
                object_pairs_hook=unique,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError("nonfinite JSON token")
                ),
            )
        except (ValueError, RecursionError, UnicodeDecodeError):
            return await error("invalid_json", "Malformed, duplicate-key or nonfinite JSON", 422)(
                scope, receive, send
            )
        consumed = False

        async def replay():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": body}
            return await receive()  # preserves real client disconnect notifications

        return await self.app(scope, replay, send)


def create_app(*, enable_quantum=None):
    enabled = (
        os.environ.get("QWS_ENABLE_LOCAL_QUANTUM") == "1"
        if enable_quantum is None
        else enable_quantum
    )
    app = FastAPI(
        title="Quantum Workload Studio — local TSP",
        version="0.1.0",
        responses={
            400: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
            503: {"model": ErrorResponse},
            504: {"model": ErrorResponse},
        },
    )
    app.add_middleware(BoundedBody)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )
    app.state.busy = False
    app.state.active_cancel = None
    app.state.last_worker = None

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(
            "invalid_input",
            "Input failed strict validation",
            422,
            [
                {"location": list(e["loc"]), "type": e["type"], "message": e["msg"]}
                for e in exc.errors()
            ],
        )

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "quantum_enabled": enabled,
            "quantum_available": importlib.util.find_spec("qiskit") is not None,
            "busy": app.state.busy,
            "concurrency": 1,
            "max_payload_bytes": MAX_BODY,
            "memory_policy": "sampled RSS; not a kernel hard cap",
        }

    async def bounded(request, callback):
        if app.state.busy:
            return error("busy", "One local job is active; retry after it finishes", 503)
        app.state.busy = True  # no await before test-and-set on this event loop
        cancel = threading.Event()
        app.state.active_cancel = cancel
        task = asyncio.create_task(asyncio.to_thread(callback, cancel))
        try:
            while not task.done():
                await asyncio.wait({task}, timeout=0.02)
                if await request.is_disconnected():
                    cancel.set()
            return await task
        except asyncio.CancelledError:
            cancel.set()
            # The thread owns worker cleanup; never release admission while it runs.
            await asyncio.shield(task)
            raise
        finally:
            cancel.set()
            if not task.done():
                await asyncio.shield(task)
            app.state.busy = False
            app.state.active_cancel = None

    @app.post("/api/problems/tsp/solve", response_model=ApiResult)
    async def solve(data: SolveRequest, request: Request):
        if data.method == "quantum_local" and not enabled:
            return error(
                "unsupported",
                "Local quantum requires server opt-in QWS_ENABLE_LOCAL_QUANTUM=1",
                400,
            )
        if (
            data.method == "quantum_local"
            and data.quantum.shots * data.quantum.max_evaluations > MAX_API_SHOTS
        ):
            return error(
                "resource_limit", "API trace budget is at most 8192 total requested shots", 400
            )
        if data.method == "quantum_local" and importlib.util.find_spec("qiskit") is None:
            return error(
                "unsupported", "Optional local quantum dependencies are not installed", 400
            )
        n = len(data.instance.city_ids)
        if (data.method == "classical" and data.solver == "exact_tsp" and n > 8) or (
            data.method == "quantum_local" and (n - 1) ** 2 > 16
        ):
            return error(
                "unsupported_size",
                "Exact mode supports <=8 cities; local quantum <=16 active bits",
                400,
            )

        def compute(cancel):
            start = time.monotonic()
            try:
                if data.method == "quantum_local":
                    options = data.quantum.model_copy(
                        update={
                            "timeout_s": data.timeout_s,
                            "memory_limit_mb": data.memory_limit_mb,
                        }
                    )
                    raw = run_local(data.instance, options, cancel=cancel)
                    app.state.last_worker = {
                        k: raw[k]
                        for k in [
                            "worker_pid",
                            "worker_exitcode",
                            "worker_alive_after_cleanup",
                            "forced_cleanup",
                        ]
                    }
                    best, s = raw["samples"]["best_feasible"], raw["samples"]
                    completed = next((e for e in raw["events"] if e["kind"] == "completed"), {})
                    optimizer = completed.get("optimizer", {})
                    q = QuantumSummary(
                        **{
                            k: s[k]
                            for k in [
                                "raw_shots",
                                "feasible_shots",
                                "invalid_shots",
                                "feasible_fraction",
                                "invalid_fraction",
                                "candidate_outcome",
                                "raw_counts",
                            ]
                        },
                        evaluations=len(raw["sample_evaluations"]),
                        optimizer_success=optimizer.get("success"),
                        optimizer_message=optimizer.get("message"),
                        exact_reference=raw["reference"]["objective"],
                        absolute_gap=raw["absolute_optimality_gap"],
                        selection_policy=raw["selection_policy"],
                    )
                    result = ApiResult(
                        instance_hash=data.instance.instance_hash(),
                        method=data.method,
                        solver_id=options.backend,
                        execution_status=raw["execution_status"],
                        outcome=s["candidate_outcome"],
                        assignment=best["assignment"] if best else None,
                        validation=best["validation"]
                        if best
                        else ValidationReport(checked=False, feasible=None, violations=[]),
                        objective=best["original_objective"] if best else None,
                        objective_unit=data.instance.distance_unit,
                        proven_optimal=False,
                        total_elapsed_s=time.monotonic() - start,
                        quantum=q,
                        worker={
                            k: raw[k]
                            for k in [
                                "worker_pid",
                                "worker_exitcode",
                                "worker_alive_after_cleanup",
                                "forced_cleanup",
                                "observed_peak_worker_rss_bytes",
                                "cleanup_elapsed_s",
                                "max_observed_watchdog_interval_s",
                                "failures",
                            ]
                        },
                        effective_options=options.model_dump(),
                    )
                else:
                    options = LocalOptions(
                        timeout_s=data.timeout_s, memory_limit_mb=data.memory_limit_mb
                    )
                    raw = supervise(
                        {
                            "instance": data.instance.model_dump(),
                            "solver": data.solver,
                            "scale": data.scale,
                            "timeout_s": data.timeout_s,
                        },
                        options,
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
                            "Local worker did not finish cleanly",
                            504 if raw["execution_status"] == "timeout" else 503,
                            [
                                {
                                    **app.state.last_worker,
                                    "process_start_call_s": raw["process_start_call_s"],
                                    "first_worker_event_elapsed_s": raw[
                                        "first_worker_event_elapsed_s"
                                    ],
                                    "cleanup_elapsed_s": raw["cleanup_elapsed_s"],
                                    "phase_events": raw["events"],
                                }
                            ],
                        )
                    solved = next(e["result"] for e in raw["events"] if e["kind"] == "completed")
                    worker_timings = next(
                        e.get("worker_timings", {})
                        for e in raw["events"]
                        if e["kind"] == "completed"
                    )
                    result = ApiResult(
                        instance_hash=solved["instance_hash"],
                        method=data.method,
                        solver_id=data.solver,
                        execution_status="completed",
                        outcome=solved["outcome"],
                        assignment=solved["assignment"],
                        validation=solved["validation"],
                        objective=solved["objective"],
                        objective_unit=solved["objective_unit"],
                        proven_optimal=solved["proven_optimal"],
                        total_elapsed_s=time.monotonic() - start,
                        worker={
                            **{k: v for k, v in raw.items() if k != "events"},
                            "stage_timings": worker_timings,
                            "phase_events": [e for e in raw["events"] if e["kind"] != "completed"],
                        },
                        effective_options=solved["options"],
                    )
                return result
            except ImportError:
                return error(
                    "unsupported", "Optional local quantum dependencies are not installed", 400
                )
            except (ValueError, OverflowError) as exc:
                return error("resource_limit", str(exc), 400)
            except TimeoutError as exc:
                return error("timeout", str(exc), 504)
            except Exception:
                return error("execution_error", "Local execution failed; no fallback was used", 503)

        return await bounded(request, compute)

    @app.post("/api/qubo/compile", response_model=QuboArtifact)
    async def compile(data: CompileRequest):
        if len(data.instance.city_ids) > 8:
            return error("unsupported_size", "QUBO compilation supports <=8 cities", 400)
        try:
            return compile_qubo(data.instance)
        except (ValueError, OverflowError) as exc:
            return error("resource_limit", str(exc), 400)

    @app.post("/api/qubo/inspect", response_model=InspectResult)
    async def inspect(data: InspectRequest):
        try:
            verify_artifact(data.instance, data.qubo)
            bits = bits_from_display(data.bits, len(data.qubo.variables))
            decoded = decode_assignment(data.instance, bits)
            return InspectResult(
                energy=data.qubo.energy(bits),
                **decoded.model_dump(),
                original_objective=evaluate_original_objective(data.instance, decoded.assignment)
                if decoded.assignment
                else None,
            )
        except (ValueError, OverflowError) as exc:
            return error("invalid_qubo", str(exc), 422)

    return app


app = create_app()
