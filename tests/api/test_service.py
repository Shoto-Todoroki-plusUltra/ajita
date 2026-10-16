"""Actual process/API tests. Injected lifecycle fixtures never supply solver results."""

import asyncio
import importlib
import json
import signal
import subprocess
import sys
import time

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from quantum_workload_studio.api.app import MAX_BODY, create_app
from quantum_workload_studio.execution.local import LocalOptions, supervise


def _completed_then_hang(send, payload):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    send.send({"kind": "completed", "result": "lifecycle test fixture only"})
    time.sleep(30)


def _error(send, payload):
    send.send({"kind": "error", "message": "injected fixture"})
    send.close()


def _memory(send, payload):
    allocation = bytearray(128 * 1024**2)
    send.send({"kind": "allocated", "bytes": len(allocation)})
    time.sleep(30)


def _sleep(send, payload):
    time.sleep(30)


def test_completed_event_is_not_clean_exit():
    result = supervise({}, LocalOptions(timeout_s=5.0), target=_completed_then_hang)
    assert result["events"][0]["kind"] == "completed"
    assert result["execution_status"] == "unclean_worker_exit"
    assert result["forced_cleanup"] and result["worker_exitcode"] != 0
    assert not result["worker_alive_after_cleanup"]


@pytest.fixture
def body(instance):
    return {"instance": instance.model_dump(), "solver": "exact_tsp", "timeout_s": 30.0}


def test_classical_environment_imports_no_quantum():
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from quantum_workload_studio.api.app import app; import sys; assert not any(k.startswith('qiskit') for k in sys.modules); print('clean')",
        ],
        text=True,
    )
    assert output.strip() == "clean"


@pytest.mark.parametrize("solver", ["exact_tsp", "ortools_tsp"])
def test_real_classical_solve(body, solver):
    with TestClient(create_app()) as client:
        response = client.post("/api/problems/tsp/solve", json={**body, "solver": solver})
    assert response.status_code == 200, response.text
    r = response.json()
    assert r["objective"] == 4 and r["validation"]["feasible"]
    assert r["execution_status"] == "completed" and r["worker"]["worker_exitcode"] == 0
    assert not r["worker"]["worker_alive_after_cleanup"] and r["total_elapsed_s"] > 0
    assert r["proven_optimal"] == (solver == "exact_tsp")


def test_health_and_opt_in(body):
    with TestClient(create_app(enable_quantum=False)) as client:
        assert client.get("/api/health").json()["concurrency"] == 1
        r = client.post("/api/problems/tsp/solve", json={**body, "method": "quantum_local"})
        assert r.status_code == 400 and r.json()["error"]["code"] == "unsupported"


def test_strict_payloads_and_origins(body):
    with TestClient(create_app()) as c:
        endpoint = "/api/problems/tsp/solve"
        for data in [
            {**body, "path": "/tmp/input"},
            {**body, "timeout_s": "1"},
            {**body, "solver": "eval"},
        ]:
            assert c.post(endpoint, json=data).status_code == 422
        assert (
            c.post(
                endpoint,
                content='{"instance":null,"instance":null}',
                headers={"content-type": "application/json"},
            ).json()["error"]["code"]
            == "invalid_json"
        )
        assert (
            c.post(
                endpoint, content='{"timeout_s":NaN}', headers={"content-type": "application/json"}
            ).status_code
            == 422
        )
        assert (
            c.post(
                endpoint, content=" " * (MAX_BODY + 1), headers={"content-type": "application/json"}
            ).status_code
            == 413
        )
        assert (
            c.post(endpoint, json=body, headers={"origin": "https://example.com"}).status_code
            == 403
        )
        assert c.post(endpoint, content="{}").status_code == 415
        bad = json.loads(json.dumps(body))
        bad["instance"]["geometry"]["distances"][0][1] = 12
        assert c.post(endpoint, json=bad).status_code == 422


def test_compile_inspect_invalid_and_canonical(body):
    with TestClient(create_app()) as c:
        qubo = c.post("/api/qubo/compile", json={"instance": body["instance"]}).json()
        r = c.post(
            "/api/qubo/inspect",
            json={"instance": body["instance"], "qubo": qubo, "bits": "100010001"},
        )
        assert r.status_code == 200 and r.json()["original_objective"] == 4
        r = c.post(
            "/api/qubo/inspect",
            json={"instance": body["instance"], "qubo": qubo, "bits": "000000000"},
        )
        assert (
            r.json()["validation"]["feasible"] is False and r.json()["original_objective"] is None
        )
        qubo["offset"] += 1
        assert (
            c.post(
                "/api/qubo/inspect",
                json={"instance": body["instance"], "qubo": qubo, "bits": "100010001"},
            ).status_code
            == 422
        )


def test_size_and_timeout(body):
    data = json.loads(json.dumps(body))
    ids = list("ABCDEFGHI")
    data["instance"].update(
        city_ids=ids,
        geometry={
            "kind": "matrix",
            "distances": [[0 if i == j else 1 for i in range(9)] for j in range(9)],
        },
    )
    with TestClient(create_app()) as c:
        assert (
            c.post("/api/problems/tsp/solve", json=data).json()["error"]["code"]
            == "unsupported_size"
        )
        assert c.post("/api/qubo/compile", json={"instance": data["instance"]}).status_code == 400
        result = c.post("/api/problems/tsp/solve", json={**body, "timeout_s": 0.001})
        assert result.status_code == 504 and result.json()["error"]["code"] == "timeout"
        assert not result.json()["error"]["details"][0]["worker_alive_after_cleanup"]


@pytest.mark.parametrize(
    "target,code",
    [(_error, "error"), (_memory, "memory_limit"), (_completed_then_hang, "unclean_worker_exit")],
)
def test_api_worker_failure_cleanup(body, monkeypatch, target, code):
    module = importlib.import_module("quantum_workload_studio.api.app")
    monkeypatch.setattr(module, "classical_worker", target)
    with TestClient(create_app()) as c:
        result = c.post("/api/problems/tsp/solve", json={**body, "memory_limit_mb": 64})
        assert result.status_code == 503 and result.json()["error"]["code"] == code
        assert not result.json()["error"]["details"][0]["worker_alive_after_cleanup"]
        assert not c.get("/api/health").json()["busy"]


def test_asgi_disconnect_and_concurrent_rejection(body, monkeypatch):
    import httpx

    module = importlib.import_module("quantum_workload_studio.api.app")
    monkeypatch.setattr(module, "classical_worker", _sleep)
    app = create_app()

    async def scenario():
        queue, output = asyncio.Queue(), []
        await queue.put({"type": "http.request", "body": json.dumps(body).encode()})

        async def send(message):
            output.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/problems/tsp/solve",
            "raw_path": b"/api/problems/tsp/solve",
            "query_string": b"",
            "headers": [(b"host", b"localhost"), (b"content-type", b"application/json")],
            "client": ("127.0.0.1", 1),
            "server": ("127.0.0.1", 8000),
        }
        task = asyncio.create_task(app(scope, queue.get, send))
        for _ in range(100):
            if app.state.busy:
                break
            await asyncio.sleep(0.01)
        assert app.state.busy
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as c:
            r = await c.post("/api/problems/tsp/solve", json=body)
            assert r.status_code == 503 and r.json()["error"]["code"] == "busy"
        await queue.put({"type": "http.disconnect"})
        await asyncio.wait_for(task, 3)
        assert not app.state.busy and not app.state.last_worker["worker_alive_after_cleanup"]
        assert app.state.last_worker["forced_cleanup"]

    asyncio.run(scenario())


def test_real_quantum_and_no_feasible_outcome(body):
    pytest.importorskip("qiskit")
    with TestClient(create_app(enable_quantum=True)) as c:
        result = c.post(
            "/api/problems/tsp/solve",
            json={
                **body,
                "method": "quantum_local",
                "quantum": {"max_evaluations": 4, "shots": 1, "seed": 1729},
            },
        )
        assert result.status_code == 200, result.text
        r = result.json()
        assert r["execution_status"] == "completed"
        assert r["quantum"]["raw_shots"] == 4
        assert sum(r["quantum"]["raw_counts"].values()) == 4
        assert not r["worker"]["worker_alive_after_cleanup"]
        assert r["quantum"]["feasible_shots"] == 0
        assert r["outcome"] == "no_feasible_sample" and r["objective"] is None
        assert r["quantum"]["absolute_gap"] is None


def test_asgi_handler_cancellation_awaits_cleanup(body, monkeypatch):
    module = importlib.import_module("quantum_workload_studio.api.app")
    monkeypatch.setattr(module, "classical_worker", _sleep)
    app = create_app()

    async def scenario():
        queue = asyncio.Queue()
        await queue.put({"type": "http.request", "body": json.dumps(body).encode()})

        async def send(message):
            pass

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/problems/tsp/solve",
            "raw_path": b"/api/problems/tsp/solve",
            "query_string": b"",
            "headers": [(b"host", b"localhost"), (b"content-type", b"application/json")],
            "client": ("127.0.0.1", 1),
            "server": ("127.0.0.1", 8000),
        }
        task = asyncio.create_task(app(scope, queue.get, send))
        for _ in range(100):
            if app.state.busy:
                break
            await asyncio.sleep(0.01)
        assert app.state.busy
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 3)
        assert not app.state.busy
        assert app.state.last_worker["forced_cleanup"]
        assert not app.state.last_worker["worker_alive_after_cleanup"]

    asyncio.run(scenario())


def test_api_memory_monitor_denial_fails_closed(body, monkeypatch):
    import psutil

    def denied(self):
        raise psutil.AccessDenied(self.pid)

    monkeypatch.setattr(psutil.Process, "memory_info", denied)
    with TestClient(create_app()) as client:
        result = client.post("/api/problems/tsp/solve", json=body)
        assert result.status_code == 503
        assert result.json()["error"]["code"] == "monitor_unavailable"
        assert not result.json()["error"]["details"][0]["worker_alive_after_cleanup"]
