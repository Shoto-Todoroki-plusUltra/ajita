from pathlib import Path

import pytest

from quantum_workload_studio.models.tsp import TspInstance

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def instance():
    return TspInstance.model_validate_json((ROOT / "examples/tsp/four_city.json").read_text())
