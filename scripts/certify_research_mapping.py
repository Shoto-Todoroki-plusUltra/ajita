"""Fixed mathematical fixture/parity certificate only; no experimental sampler."""

import hashlib
import json
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

from quantum_workload_studio.execution.local import LocalOptions, supervise
from quantum_workload_studio.execution.mapping_certificate import certificate_worker


def main():
    root = Path(__file__).resolve().parents[1]
    result = supervise(
        {"root": str(root)},
        LocalOptions(timeout_s=60.0, memory_limit_mb=512),
        target=certificate_worker,
    )
    output = root / "evidence/3bm/mapping-certificate.json"
    output.parent.mkdir(exist_ok=True)
    result["provenance"] = {
        "kind": "mathematical mapping tests only, no study data",
        "command": [sys.executable, "scripts/certify_research_mapping.py"],
        "python": sys.version,
        "platform": platform.platform(),
        "source_commit_at_run": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "packages": {
            p: version(p)
            for p in [
                "qiskit",
                "qiskit-aer",
                "numpy",
                "scipy",
                "ortools",
                "pydantic",
                "psutil",
                "pytest",
            ]
        },
        "source_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "src").rglob("*.py"))
        },
        "protocol_sha256": hashlib.sha256(
            (root / "docs/PHASE3_EXPERIMENT_PROTOCOL.md").read_bytes()
        ).hexdigest(),
        "lock_sha256": hashlib.sha256(
            (root / "requirements/api-quantum-macos-arm64-py312.lock").read_bytes()
        ).hexdigest(),
        "sampler_execution": "not authorized, not performed",
        "guard_scope": "fixed certificate worker, 60s (within protocol 120s maximum), sampled 512 MiB RSS; not a hard memory/deadline guarantee",
    }
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    successful = result["execution_status"] == "completed"
    certificate = next(
        (e["certificate"] for e in result["events"] if e["kind"] == "completed"), None
    )
    print(
        json.dumps(
            {
                "output": str(output.relative_to(root)),
                "execution_status": result["execution_status"],
                "basis_rows": certificate["basis_rows"] if certificate else None,
                "sampler_calls": certificate["sampler_calls"] if certificate else None,
                "worker_exitcode": result["worker_exitcode"],
                "forced_cleanup": result["forced_cleanup"],
                "worker_alive_after_cleanup": result["worker_alive_after_cleanup"],
            },
            indent=2,
        )
    )
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
