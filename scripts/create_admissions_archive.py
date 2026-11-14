"""Curated source export; private research history is never implicitly published."""

import argparse
import getpass
import importlib.util
import json
import re
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "review_archive", Path(__file__).with_name("create_review_archive.py")
)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)
DOCS = {
    "DEMO.md",
    "TECHNICAL_OVERVIEW.md",
    "VERIFICATION.md",
    "ADMISSIONS_BRIEF.md",
    "LICENSE_OPTIONS.md",
    "RELEASE_NOTES.md",
    "ADMISSIONS_PREVIEW_REPORT.md",
}
DENIED = {
    "src/quantum_workload_studio/execution/local_b1.py",
    "scripts/smoke_b1_local.py",
    "tests/b1_no_shots_policy.py",
    "tests/quantum/test_local_b1.py",
}
ROOTS = {"src", "tests", "requirements", "examples", "schemas", "frontend", "scripts"}
FILES = {
    "README.md",
    "pyproject.toml",
    "AGENTS.md",
    "PROJECT_BRIEF.md",
    ".gitignore",
    ".github/workflows/checks.yml",
    ".githooks/pre-commit",
}


def selected(name):
    p = Path(name)
    if (
        name in DENIED
        or not archive.safe_path(name)
        or any(part in {"__MACOSX", ".DS_Store"} for part in p.parts)
    ):
        return False
    return (
        name in FILES
        or p.parts[0] in ROOTS
        or (len(p.parts) == 2 and p.parts[0] == "docs" and p.name in DOCS)
        or name in {"docs/images/tsp-classical.png", "docs/images/b1-timetable.png"}
        or name.startswith("evidence/admissions-preview/public/")
    )


def privacy_scan(entries, *, username=None):
    """Targeted publication checks, not an exhaustive security certification."""
    username = getpass.getuser() if username is None else username
    issues = []
    patterns = [
        rb"/" + rb"Users/[^/\s\"']+",
        rb"(?:gh[pousr]_|sk-proj-|xox[baprs]-)[A-Za-z0-9_-]{20,}",
        rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        rb"[\w.+-]{1,64}@(?:gmail|outlook|hotmail|icloud|yahoo)\.[A-Za-z]+",
    ]
    for name, data in entries.items():
        if not selected(name):
            issues.append({"path": name, "reason": "not in curated publication set"})
        if len(data) > 12 * 1024**2:
            issues.append({"path": name, "reason": "oversized publication member"})
            continue  # Refuse size before running any text scan.
        if name.endswith(".png"):
            continue  # actual screenshots require visual inspection, not text scanning
        if any(re.search(pattern, data) for pattern in patterns):
            issues.append({"path": name, "reason": "private path/contact/credential marker"})
        if (
            username
            and len(username) > 3
            and re.search(rb"\b" + re.escape(username.encode()) + rb"\b", data, re.I)
        ):
            issues.append({"path": name, "reason": "local username marker"})
    if issues:
        raise ValueError(json.dumps(issues))
    return {
        "files_scanned": len(entries),
        "marker_findings": [],
        "screenshots": "manual visual inspection required",
        "scope": "targeted markers only",
    }


def build(output, entries, commit):
    public = {n: b for n, b in entries.items() if selected(n)}
    audit = privacy_scan(public)
    public["PUBLIC_EXPORT.json"] = (
        json.dumps(
            {
                "kind": "curated_admissions_source_not_git_history",
                "source_commit": commit,
                "license": "not_selected",
                "published": False,
                "scan": audit,
                "excluded": [
                    "private historical logs/reports",
                    "Git history/internals",
                    "unfinished B1 quantum runner",
                    "installed dependencies/caches/builds",
                    "review ZIPs",
                ],
            },
            indent=2,
        )
        + "\n"
    ).encode()
    return archive.build(output, public, commit)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit], cwd=root, text=True
    ).splitlines()
    entries = {
        n: subprocess.check_output(["git", "show", f"{commit}:{n}"], cwd=root)
        for n in names
        if selected(n)
    }
    result = build(args.output, entries, commit)
    print(
        json.dumps(
            {
                "commit": commit,
                "archive": str(args.output),
                "sha256": result["archive_sha256"],
                "members": len(result["members_sha256"]),
                "verified": True,
            },
            indent=2,
        )
    )
