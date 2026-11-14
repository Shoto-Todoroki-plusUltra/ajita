"""Publication packaging tests; no solver or sampler work."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "admissions_archive", Path(__file__).parents[1] / "scripts/create_admissions_archive.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_curated_export_retains_hidden_config_and_omits_private_evidence(tmp_path):
    files = {p: b"configuration\n" for p in module.archive.REQUIRED}
    files |= {
        "README.md": b"preview\n",
        "evidence/phase2/private.log": b"private observation",
        "review-snapshots/old.zip": b"old archive",
        "src/quantum_workload_studio/execution/local_b1.py": b"unaccepted draft",
        "frontend/node_modules/pkg/a": b"installed",
    }
    result = module.build(tmp_path / "preview.zip", files, "test-only-snapshot")
    with zipfile.ZipFile(tmp_path / "preview.zip") as z:
        assert all(module.archive.PREFIX + p in z.namelist() for p in module.archive.REQUIRED)
        assert not any(
            "private.log" in p or "node_modules" in p or "local_b1.py" in p for p in z.namelist()
        )
        assert (
            json.loads(z.read(module.archive.PREFIX + "PUBLIC_EXPORT.json"))["published"] is False
        )
    module.archive.verify(tmp_path / "preview.zip", result)


@pytest.mark.parametrize("data", [b"/Users/" + b"developer/private", b"ghp_" + b"A" * 36])
def test_publication_scan_refuses_private_markers(data):
    with pytest.raises(ValueError, match="marker"):
        module.privacy_scan({"README.md": data}, username="test-user")


def test_publication_scan_refuses_username_and_oversized_text():
    with pytest.raises(ValueError, match="username"):
        module.privacy_scan({"README.md": b"local-developer"}, username="local-developer")
    with pytest.raises(ValueError, match="oversized"):
        module.privacy_scan({"README.md": b"x" * (12 * 1024**2 + 1)}, username="test-user")
