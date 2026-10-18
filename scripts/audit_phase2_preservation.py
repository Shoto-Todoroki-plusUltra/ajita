"""Compare accepted tracked evidence/locks byte-for-byte; never read untracked inputs."""

import hashlib
import json
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

BASELINE = "2f66cdf"


def main():
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASELINE, "evidence", "requirements"], text=True
    ).splitlines()
    checks = []
    for path in paths:
        original = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"])
        current = Path(path).read_bytes()
        if original != current:
            raise ValueError(f"historical evidence/lock changed: {path}")
        checks.append({"path": path, "sha256": hashlib.sha256(current).hexdigest()})
    print(
        json.dumps(
            {
                "baseline": BASELINE,
                "preserved_tracked_files": len(checks),
                "all_identical": True,
                "files": checks,
                "platform": platform.platform(),
                "python": sys.version,
                "packages": {
                    p: version(p)
                    for p in [
                        "ortools",
                        "pydantic",
                        "fastapi",
                        "uvicorn",
                        "starlette",
                        "httpx",
                        "psutil",
                        "pytest",
                        "ruff",
                    ]
                },
                "sw_vers": subprocess.check_output(["sw_vers"], text=True),
                "uname": subprocess.check_output(["uname", "-mrs"], text=True),
                "install_policy": "Existing pinned classical and optional environments reused; no dependency or lock versions changed in Phase 2.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
