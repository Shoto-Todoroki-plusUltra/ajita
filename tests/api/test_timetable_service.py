"""Real B1 solves plus lifecycle fault injection (never fake solver answers)."""

import asyncio
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Reuse only worker lifecycle fault fixtures from Phase 1.
from test_service import _completed_then_hang, _error, _memory, _sleep

from quantum_workload_studio.api.app import create_app


def instance_data():
    return json.loads(
        (Path(__file__).resolve().parents[2] / "examples/timetable/tiny.json").read_text()
    )


@pytest.mark.parametrize("solver", ["cp_sat", "enumeration"])
def test_real_solver(solver):
    with TestClient(create_app()) as c:
        r = c.post(
            "/api/problems/timetable/solve",
            json={"instance": instance_data(), "solver": solver, "timeout_s": 20.0},
        )
    assert r.status_code == 200, r.text
    answer = r.json()
    assert answer["result"]["objective"] == 1 and answer["result"]["proven_optimal"]
    assert answer["result"]["best_objective_bound"] == 1
    assert answer["worker"]["worker_exitcode"] == 0
    assert not answer["worker"]["worker_alive_after_cleanup"]
    import_time = answer["worker"]["stage_timings"]["ortools_import_s"]
    assert (import_time is None) == (solver == "enumeration")


def test_qubo_inspection_and_validation():
    i = instance_data()
    with TestClient(create_app()) as c:
        q = c.post("/api/problems/timetable/compile", json={"instance": i}).json()
        assert q["penalty_sufficient"] and q["penalty"] == 6
        for bits, feasible, cost in [
            ("1001", True, 1),
            ("1010", False, None),
            ("0000", False, None),
        ]:
            r = c.post(
                "/api/problems/timetable/inspect", json={"instance": i, "qubo": q, "bits": bits}
            )
            assert r.status_code == 200, r.text
            assert r.json()["validation"]["feasible"] == feasible
            assert r.json()["original_objective"] == cost
        q["offset"] += 1
        assert (
            c.post(
                "/api/problems/timetable/inspect", json={"instance": i, "qubo": q, "bits": "1001"}
            ).status_code
            == 422
        )
        checked = c.post(
            "/api/problems/timetable/validate",
            json={"instance": i, "assignment": {"assignments": []}},
        ).json()
        assert (
            len(checked["validation"]["violations"]) == 2 and checked["original_objective"] is None
        )
        for changed in [
            {"method": "quantum_local"},
            {"solver": "eval"},
            {"timeout_s": "20"},
            {"path": "/tmp/x"},
        ]:
            assert (
                c.post("/api/problems/timetable/solve", json={"instance": i, **changed}).status_code
                == 422
            )


def test_infeasible_and_size():
    i = instance_data()
    i["rooms"][0]["capacity"] = 0
    with TestClient(create_app()) as c:
        r = c.post("/api/problems/timetable/solve", json={"instance": i, "timeout_s": 20.0})
        assert r.status_code == 200, r.text
        assert r.json()["result"]["native_status"] == "INFEASIBLE"
        q = c.post("/api/problems/timetable/compile", json={"instance": i}).json()
        assert q["variables"] == []
        inspected = c.post(
            "/api/problems/timetable/inspect", json={"instance": i, "qubo": q, "bits": ""}
        )
        assert inspected.status_code == 200 and not inspected.json()["validation"]["feasible"]
        i = instance_data()
        i["slots"] = [{"id": f"s{k}", "label": str(k), "order": k} for k in range(10)]
        i["preferences"] = []
        assert (
            c.post("/api/problems/timetable/compile", json={"instance": i}).json()["error"]["code"]
            == "unsupported_size"
        )
        i["courses"] *= 10
        for k, course in enumerate(i["courses"]):
            i["courses"][k] = {**course, "id": f"c{k}"}
        assert (
            c.post(
                "/api/problems/timetable/solve", json={"instance": i, "solver": "enumeration"}
            ).json()["error"]["code"]
            == "unsupported_size"
        )


@pytest.mark.parametrize(
    "target,code",
    [
        (_error, "error"),
        (_memory, "memory_limit"),
        (_completed_then_hang, "unclean_worker_exit"),
        (_sleep, "timeout"),
    ],
)
def test_worker_cleanup(monkeypatch, target, code):
    module = importlib.import_module("quantum_workload_studio.api.timetable")
    monkeypatch.setattr(module, "classical_worker", target)
    with TestClient(create_app()) as c:
        r = c.post(
            "/api/problems/timetable/solve",
            json={"instance": instance_data(), "timeout_s": 1.5, "memory_limit_mb": 64},
        )
        assert r.status_code == (504 if code == "timeout" else 503), r.text
        assert r.json()["error"]["code"] == code
        assert not r.json()["error"]["details"][0]["worker_alive_after_cleanup"]
        assert not c.get("/api/health").json()["busy"]


@pytest.mark.parametrize("cancel_task", [False, True])
def test_cross_domain_admission_disconnect_and_cancellation(monkeypatch, cancel_task):
    import httpx

    module = importlib.import_module("quantum_workload_studio.api.timetable")
    monkeypatch.setattr(module, "classical_worker", _sleep)
    app = create_app()

    async def scenario():
        queue = asyncio.Queue()
        await queue.put(
            {
                "type": "http.request",
                "body": json.dumps({"instance": instance_data(), "timeout_s": 20.0}).encode(),
            }
        )

        async def send(message):
            pass

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/problems/timetable/solve",
            "raw_path": b"/api/problems/timetable/solve",
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
        tsp = json.loads(
            (Path(__file__).resolve().parents[2] / "examples/tsp/four_city.json").read_text()
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as c:
            # Any valid TSP request must share the timetable admission gate.
            r = await c.post(
                "/api/problems/tsp/solve",
                json={"instance": tsp, "solver": "exact_tsp"},
            )
            assert r.status_code == 503 and r.json()["error"]["code"] == "busy"
        if cancel_task:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 3)
        else:
            await queue.put({"type": "http.disconnect"})
            await asyncio.wait_for(task, 3)
        assert not app.state.busy and not app.state.last_worker["worker_alive_after_cleanup"]

    asyncio.run(scenario())


def test_cli_and_quantum_free_import(tmp_path):
    path = Path(__file__).resolve().parents[2] / "examples/timetable/tiny.json"
    base = [sys.executable, "-m", "quantum_workload_studio.cli", "timetable"]
    compiled = subprocess.run(
        [*base, "compile", "--instance", str(path)], capture_output=True, text=True
    )
    assert compiled.returncode == 0, compiled.stderr
    q = tmp_path / "q.json"
    q.write_text(compiled.stdout)
    inspected = subprocess.run(
        [*base, "inspect", "--instance", str(path), "--qubo", str(q), "--bits", "1001"],
        capture_output=True,
        text=True,
    )
    assert inspected.returncode == 0 and json.loads(inspected.stdout)["original_objective"] == 1
    solved = subprocess.run(
        [*base, "solve", "--instance", str(path), "--timeout-s", "20"],
        capture_output=True,
        text=True,
    )
    assert solved.returncode == 0, solved.stdout + solved.stderr
    assert json.loads(solved.stdout)["result"]["native_status"] == "OPTIMAL"
    output = subprocess.check_output(
        [
            sys.executable,
            "-c",
            "from quantum_workload_studio.api.app import app; import sys; assert not any(n.startswith('qiskit') for n in sys.modules); print('clean')",
        ],
        text=True,
    )
    assert output.strip() == "clean"
