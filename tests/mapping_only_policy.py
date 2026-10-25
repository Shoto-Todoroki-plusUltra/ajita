"""Explicit opt-in pytest safety policy for the owner's mapping-only gate.

Loaded with -p mapping_only_policy; never alters normal historical test selection.
"""

import importlib.util
import json
from pathlib import Path

import pytest

EXCLUDED = {
    "tests/quantum/test_operator.py::test_permuted_measurements_and_physical_layout[statevector]",
    "tests/quantum/test_operator.py::test_permuted_measurements_and_physical_layout[aer]",
    "tests/quantum/test_local.py::test_actual_deadline_retains_honest_no_samples",
    "tests/quantum/test_local.py::test_real_qaoa_reproducible_and_bounded",
    "tests/quantum/test_local.py::test_local_cli_failure_artifacts",
    "tests/api/test_service.py::test_real_quantum_and_no_feasible_outcome",
}
ATTEMPTS = []
DEFERRED = []


def pytest_addoption(parser):
    parser.addoption("--mapping-policy-evidence", default=None)


def pytest_collection_modifyitems(config, items):
    selected, deferred = [], []
    for item in items:
        if item.nodeid in EXCLUDED:
            deferred.append(item)
            DEFERRED.append(item.nodeid)
        else:
            selected.append(item)
    items[:] = selected
    config.hook.pytest_deselected(items=deferred)


@pytest.fixture(autouse=True)
def forbid_sampler_execution(monkeypatch):
    def denied(*args, **kwargs):
        ATTEMPTS.append("forbidden sampler or default QAOA worker invocation")
        raise AssertionError("Mapping-only approval forbids sampler/QAOA execution")

    from quantum_workload_studio.execution import local

    monkeypatch.setattr(local, "_qaoa_worker", denied)
    if importlib.util.find_spec("qiskit") is not None:
        from qiskit.primitives import StatevectorSampler

        monkeypatch.setattr(StatevectorSampler, "run", denied)
    if importlib.util.find_spec("qiskit_aer") is not None:
        from qiskit_aer.primitives import SamplerV2

        monkeypatch.setattr(SamplerV2, "run", denied)


def pytest_sessionfinish(session, exitstatus):
    path = session.config.getoption("--mapping-policy-evidence")
    if path:
        Path(path).write_text(
            json.dumps(
                {
                    "deferred_not_passed": DEFERRED,
                    "forbidden_call_attempts": ATTEMPTS,
                    "pytest_exitstatus": int(exitstatus),
                    "policy": "No real sampler, optimizer experiment or default QAOA worker execution",
                },
                indent=2,
            )
            + "\n"
        )
    if ATTEMPTS:
        session.exitstatus = 1
