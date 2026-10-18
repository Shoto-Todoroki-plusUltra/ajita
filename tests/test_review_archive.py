"""Archive contract tests include hidden files, and reject extra/tampered data."""

import importlib.util
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "review_archive", Path(__file__).parents[1] / "scripts/create_review_archive.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def files():
    return {name: b"test configuration\n" for name in module.REQUIRED} | {
        "README.md": b"review fixture\n"
    }


def test_required_hidden_files_and_exact_member_hashes(tmp_path):
    archive = tmp_path / "review.zip"
    manifest = module.build(archive, files(), "unit-test-not-a-production-commit")
    assert len(manifest["members_sha256"]) == 5
    assert set(manifest["required_hidden_files"]) == {module.PREFIX + n for n in module.REQUIRED}
    assert module.EMBEDDED in manifest["members_sha256"]
    with zipfile.ZipFile(archive, "a") as z:
        z.writestr(module.PREFIX + "unlisted.txt", "unlisted fixture")
    with pytest.raises(ValueError, match="member set"):
        module.verify(archive, manifest)


def test_missing_configuration_and_git_internals_are_refused(tmp_path):
    entries = files()
    entries.pop(".githooks/pre-commit")
    with pytest.raises(ValueError, match="required tracked"):
        module.build(tmp_path / "missing.zip", entries, "test")
    for bad in [
        ".git/config",
        "review-history.bundle",
        ".aws/credentials",
        ".venv/site.py",
        "frontend/node_modules/x.js",
    ]:
        with pytest.raises(ValueError, match="refusing unsafe"):
            module.build(tmp_path / "bad.zip", files() | {bad: b"test"}, "test")


def test_hash_tampering_is_detected(tmp_path):
    archive = tmp_path / "review.zip"
    manifest = module.build(archive, files(), "test")
    manifest["members_sha256"][module.PREFIX + "README.md"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        module.verify(archive, manifest)
