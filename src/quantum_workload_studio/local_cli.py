"""Research-only CLI for authorized 1B experiments; original qws CLI unchanged."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import sys
from datetime import datetime, timezone

from quantum_workload_studio.cli import read_json
from quantum_workload_studio.evidence import write_json
from quantum_workload_studio.models.tsp import TspInstance


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded local QAOA research experiment, no cloud or fallback")
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=["statevector", "aer"], default="statevector")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--shots", type=int, default=256)
    parser.add_argument("--evaluations", type=int, default=16)
    parser.add_argument("--timeout-s", type=float, default=60.0)
    parser.add_argument("--memory-mb", type=int, default=1024)
    args = parser.parse_args(argv)
    try:
        from quantum_workload_studio.execution.local import LocalOptions, run_local
        instance = TspInstance.model_validate(read_json(args.instance))
        result = run_local(instance, LocalOptions(backend=args.backend, seed=args.seed, shots=args.shots,
                           max_evaluations=args.evaluations, timeout_s=args.timeout_s, memory_limit_mb=args.memory_mb))
        exit_status = 0 if result["execution_status"] == "completed" else 1
    except (ValueError, ImportError, TimeoutError, OSError) as error:
        result = {"execution_status": "preflight_error", "error_type": type(error).__name__, "message": str(error)}
        exit_status = 2
    root = Path(__file__).resolve().parents[2]
    result["provenance"] = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, "-m", "quantum_workload_studio.local_cli", *(argv if argv is not None else sys.argv[1:])],
        "python": sys.version, "platform": platform.platform(), "architecture": platform.machine(),
        "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
        "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/"src").rglob("*.py"))},
        "lock_sha256": hashlib.sha256((root/"requirements/quantum-macos-arm64-py312.lock").read_bytes()).hexdigest()}
    write_json(args.output, result)
    print(json.dumps({"output": str(args.output), "execution_status": result["execution_status"],
                      "samples": {k: v for k, v in result.get("samples", {}).items()
                                  if k not in ["decoded_unique_samples", "best_feasible", "raw_counts"]}}, indent=2))
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
