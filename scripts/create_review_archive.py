"""Sanitized committed source ZIP, with exact archive-member hashes.

No Git objects/bundles or untracked files are packaged. Required hidden project
configuration is explicit, rather than filtered by a dotfile glob.
"""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

REQUIRED = {".gitignore", ".github/workflows/checks.yml", ".githooks/pre-commit"}
PREFIX = "quantum-workload-studio/"
EMBEDDED = PREFIX + "ARCHIVE_MANIFEST.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(name):
    path = PurePosixPath(name)
    forbidden = {
        ".git",
        ".aws",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        ".ruff_cache",
        "test-results",
        "review-snapshots",
    }
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not any(p in forbidden or p.startswith((".venv", ".env", ".tools")) for p in path.parts)
        and path.suffix.lower() not in {".bundle", ".zip", ".pem", ".key", ".p12", ".pyc"}
    )


def verify(archive, manifest):
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest["members_sha256"]):
            raise ValueError("archive member set differs from external manifest")
        for name, sha in manifest["members_sha256"].items():
            if digest(z.read(name)) != sha:
                raise ValueError(f"archive member hash mismatch: {name}")
        if z.testzip() is not None:
            raise ValueError("archive CRC verification failed")
    if digest(Path(archive).read_bytes()) != manifest["archive_sha256"]:
        raise ValueError("whole archive hash mismatch")


def build(archive, entries, commit):
    if not REQUIRED <= set(entries):
        raise ValueError(
            f"required tracked configuration absent: {sorted(REQUIRED - set(entries))}"
        )
    for name, content in entries.items():
        if not safe_path(name):
            raise ValueError(f"refusing unsafe/unrelated archive member: {name}")
        # Targeted credential checks; not represented as an exhaustive secret audit.
        if re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content):
            raise ValueError(f"private-key marker in {name}")
        if re.search(rb"https?://[^/\s]+:[^/\s]+@", content):
            raise ValueError(f"credential-bearing URL in {name}")
    payload = {PREFIX + name: digest(data) for name, data in sorted(entries.items())}
    inside = {
        "schema_version": 1,
        "commit": commit,
        "payload_members_sha256": payload,
        "manifest_self": "This embedded manifest is excluded from its own hash map; the external manifest hashes every ZIP member including this file.",
        "exclusions": [
            "Git internals/history bundles",
            "untracked files",
            "credentials",
            "installed environments/modules",
            "build caches",
        ],
    }
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=(2026, 10, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (
                0o100755 if name == ".githooks/pre-commit" or name.endswith(".sh") else 0o100644
            ) << 16
            z.writestr(info, data)
        z.writestr(EMBEDDED, json.dumps(inside, indent=2, sort_keys=True) + "\n")
    # Build this from actual ZIP bytes/member inventory, not the working tree.
    with zipfile.ZipFile(archive) as z:
        members = {name: digest(z.read(name)) for name in z.namelist()}
    outside = {
        "schema_version": 1,
        "commit": commit,
        "archive_file": archive.name,
        "archive_sha256": digest(archive.read_bytes()),
        "members_sha256": members,
        "required_hidden_files": {PREFIX + n: members[PREFIX + n] for n in sorted(REQUIRED)},
        "embedded_manifest_self_hash_included": True,
        "git_internals_included": False,
    }
    verify(archive, outside)
    Path(str(archive) + ".manifest.json").write_text(
        json.dumps(outside, indent=2, sort_keys=True) + "\n"
    )
    Path(str(archive) + ".sha256").write_text(
        outside["archive_sha256"] + "  " + archive.name + "\n"
    )
    return outside


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit], cwd=root, text=True
    ).splitlines()
    entries = {
        name: subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=root)
        for name in names
    }
    result = build(args.output, entries, commit)
    print(
        json.dumps(
            {
                "archive": str(args.output),
                "commit": commit,
                "members": len(result["members_sha256"]),
                "sha256": result["archive_sha256"],
                "verified": True,
            }
        )
    )
