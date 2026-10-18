"""Same tiny job under pytest scheduling; real worker, fixed 20-second cap."""

import json
import os
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from quantum_workload_studio.api.app import create_app


@pytest.mark.parametrize("repeat", range(3))
def test_stage_timing_measurements(instance, repeat):
    with TestClient(create_app(enable_quantum=False)) as client:
        response = client.post(
            "/api/problems/tsp/solve",
            json={"instance": instance.model_dump(), "solver": "ortools_tsp", "timeout_s": 20.0},
        )
    # Preserve failures before asserting, if this is an explicitly recorded audit.
    output = os.environ.get("QWS_AUDIT_EVIDENCE")
    if output:
        Path(output).mkdir(parents=True, exist_ok=True)
        (Path(output) / f"pytest-scheduling-{repeat}.json").write_text(
            json.dumps(
                {
                    "context": "pytest/TestClient scheduling; fresh spawned worker; 20-second unchanged cap",
                    "http_status": response.status_code,
                    "response": response.json(),
                },
                indent=2,
            )
            + "\n"
        )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["objective"] == 4 and result["validation"]["feasible"]
    worker = result["worker"]
    timing = worker["stage_timings"]
    assert 0 <= worker["process_start_call_s"] <= worker["first_worker_event_elapsed_s"]
    assert 0 <= timing["ortools_import_s"] < worker["compute_elapsed_s"]
    assert 0 <= timing["native_solver_s"] <= timing["dispatch_validation_model_solver_s"]
    assert not worker["worker_alive_after_cleanup"] and not worker["forced_cleanup"]
    assert worker["worker_exitcode"] == 0
