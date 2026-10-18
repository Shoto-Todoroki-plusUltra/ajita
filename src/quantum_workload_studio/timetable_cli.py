"""B1 CLI uses the same validated service and killable supervisor as HTTP."""

import argparse
import json
import sys
from pathlib import Path

from quantum_workload_studio.execution.local import LocalOptions, supervise
from quantum_workload_studio.models.timetable import (
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.qubo.timetable import (
    TimetableQubo,
    compile_qubo,
    decode,
    verify_artifact,
)
from quantum_workload_studio.services.timetable import classical_worker


def main(argv):
    # Imported here to avoid a module-initialization cycle.
    from quantum_workload_studio.cli import read_json

    parser = argparse.ArgumentParser(description="B1 classroom timetabling")
    parser.add_argument("operation", choices=["solve", "compile", "inspect", "validate"])
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--solver", choices=["cp_sat", "enumeration"], default="cp_sat")
    parser.add_argument("--timeout-s", type=float, default=10.0)
    parser.add_argument("--memory-limit-mb", type=int, default=512)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--penalty", type=int)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--qubo", type=Path)
    parser.add_argument("--bits", help="leftmost is variable 0 (B1 index order)")
    parser.add_argument("--assignment", type=Path)
    args = parser.parse_args(argv)
    try:
        instance = TimetableInstance.model_validate(read_json(args.instance))
        if args.operation == "solve":
            if not 0 <= args.seed < 2**31:
                raise ValueError("seed out of range")
            options = LocalOptions(timeout_s=args.timeout_s, memory_limit_mb=args.memory_limit_mb)
            raw = supervise(
                {
                    "instance": instance.model_dump(),
                    "solver": args.solver,
                    "seed": args.seed,
                    "timeout_s": args.timeout_s,
                },
                options,
                target=classical_worker,
            )
            payload = {
                "execution": raw,
                "result": next(
                    (e["result"] for e in raw["events"] if e["kind"] == "completed"), None
                ),
            }
        elif args.operation == "compile":
            payload = compile_qubo(instance, penalty=args.penalty, scale=args.scale).model_dump()
        elif args.operation == "inspect":
            if args.qubo is None or args.bits is None:
                raise ValueError("inspect requires --qubo and --bits")
            q = TimetableQubo.model_validate(read_json(args.qubo))
            verify_artifact(instance, q)
            bits = parse_bits(args.bits, len(q.variables))
            payload = {"energy": q.energy(bits), **decode(instance, q, bits).model_dump()}
        else:
            if args.assignment is None:
                raise ValueError("validate requires --assignment")
            assignment = TimetableAssignment.model_validate(read_json(args.assignment))
            validation = validate_assignment(instance, assignment)
            payload = {
                "validation": validation.model_dump(),
                "original_objective": original_objective(instance, assignment)
                if validation.feasible
                else None,
            }
        text = json.dumps(payload, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(text)
        else:
            print(text, end="")
        return 0 if args.operation != "solve" or raw["execution_status"] == "completed" else 2
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2


def parse_bits(text, size):
    if len(text) != size or any(c not in "01" for c in text):
        raise ValueError("bits must match canonical variable count in index order")
    return [int(c) for c in text]
