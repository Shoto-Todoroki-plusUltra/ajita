"""Bounded 1C reliability investigation, not a comparative solver benchmark.

Fresh processes do not imply flushed OS/disk caches. No timeout increase, cache
purge, dependency reinstall, fixture substitution or algorithm changes occur.
"""

import argparse
import importlib.metadata
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path


def server(marker, port):
    started = time.monotonic()
    import uvicorn

    uvicorn_seconds = time.monotonic() - started
    started = time.monotonic()
    from quantum_workload_studio.api.app import create_app

    api_seconds = time.monotonic() - started
    Path(marker).write_text(
        json.dumps({"uvicorn_import_s": uvicorn_seconds, "api_module_import_s": api_seconds})
    )
    uvicorn.run(
        create_app(enable_quantum=False),
        host="127.0.0.1",
        port=port,
        workers=1,
        log_level="warning",
    )


def audit(output):
    # HTTP client import is in the driver, never a warmup of the server/worker SDK.
    import httpx

    from quantum_workload_studio.execution.local import LocalOptions, supervise
    from quantum_workload_studio.services.tsp import classical_worker

    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    instance = json.loads((root / "examples/tsp/four_city.json").read_text())
    data = {
        "policy": {
            "fresh_servers": 3,
            "requests_per_server": 2,
            "request_deadline_s": 20.0,
            "server_startup_deadline_s": 10,
            "whole_audit_deadline_s": 240,
            "cache_claim": "First observed process/start in this audit; OS caches not flushed; not first-ever machine import",
            "warmed": "same server, fresh spawned worker for every request",
            "scope": "tiny OR-Tools API reliability only; not Phase 3 benchmarks",
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ["fastapi", "uvicorn", "pydantic", "ortools", "psutil", "httpx"]
            },
        },
        "servers": [],
        "standalone_workers": [],
    }
    beginning = time.monotonic()

    def save():
        (output / "cold-start.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")

    for index in range(3):
        if time.monotonic() - beginning > 180:
            data["stopped"] = "whole-audit guard before next server"
            break
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        marker = output / f"server-{index}-imports.json"
        record = {
            "index": index,
            "cold_label": "first observed API process"
            if index == 0
            else "repeat fresh API process",
            "requests": [],
        }
        data["servers"].append(record)
        start = time.monotonic()
        with (output / f"server-{index}.log").open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--server",
                    str(marker),
                    "--port",
                    str(port),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            record["popen_call_s"] = time.monotonic() - start
            try:
                with httpx.Client(
                    base_url=f"http://127.0.0.1:{port}", timeout=23.0, trust_env=False
                ) as client:
                    ready = False
                    while time.monotonic() - start < 10 and process.poll() is None:
                        try:
                            ready = client.get("/api/health", timeout=0.25).status_code == 200
                            if ready:
                                break
                        except httpx.HTTPError:
                            pass
                        time.sleep(0.025)
                    record["startup_to_health_s"] = time.monotonic() - start
                    record["startup_ready"] = ready
                    record["imports"] = json.loads(marker.read_text()) if marker.exists() else None
                    if ready:
                        for request_index in range(2):
                            t = time.monotonic()
                            observation = {
                                "label": "first request/fresh worker"
                                if request_index == 0
                                else "warmed server/fresh worker"
                            }
                            try:
                                response = client.post(
                                    "/api/problems/tsp/solve",
                                    json={
                                        "instance": instance,
                                        "solver": "ortools_tsp",
                                        "timeout_s": 20.0,
                                    },
                                )
                                observation.update(
                                    http_status=response.status_code, response=response.json()
                                )
                            except (httpx.HTTPError, ValueError) as exc:
                                observation.update(error_type=type(exc).__name__, message=str(exc))
                            observation["driver_http_wall_s"] = time.monotonic() - t
                            record["requests"].append(observation)
                            save()
            finally:
                cleanup = time.monotonic()
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
                record.update(
                    server_cleanup_s=time.monotonic() - cleanup, server_exitcode=process.returncode
                )
                save()
    for index in range(3):
        if time.monotonic() - beginning > 215:
            data["stopped"] = "whole-audit guard before standalone worker"
            break
        result = supervise(
            {"instance": instance, "solver": "ortools_tsp", "scale": 1000, "timeout_s": 20.0},
            LocalOptions(timeout_s=20.0, memory_limit_mb=512),
            target=classical_worker,
        )
        data["standalone_workers"].append(
            {"index": index, "context": "sequential driver main thread, no pytest/ASGI", **result}
        )
        save()
    data["audit_elapsed_s"] = time.monotonic() - beginning
    save()
    print(
        json.dumps(
            {
                "servers": len(data["servers"]),
                "statuses": [
                    [r.get("http_status", r.get("error_type")) for r in s["requests"]]
                    for s in data["servers"]
                ],
                "standalone_statuses": [r["execution_status"] for r in data["standalone_workers"]],
                "elapsed_s": data["audit_elapsed_s"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--server")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    if args.server:
        server(args.server, args.port)
    else:
        audit(args.output)
