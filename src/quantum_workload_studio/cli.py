"""Minimal classical solve/compile/inspect/evidence CLI for checkpoint 1A."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from quantum_workload_studio.classical.tsp import exact_solve, ortools_solve
from quantum_workload_studio.domains.tsp import TspProblem
from quantum_workload_studio.evidence import generate_evidence, write_json
from quantum_workload_studio.models.tsp import evaluate_original_objective
from quantum_workload_studio.qubo.tsp import QuboArtifact, bits_from_display, compile_qubo, decode_assignment, verify_artifact


def read_json(path: Path):
    if path.stat().st_size > 2*1024*1024:
        raise ValueError("JSON input exceeds 2 MiB")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")

    return json.loads(path.read_text(), object_pairs_hook=unique, parse_constant=invalid_constant)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Checkpoint 1A: classical mathematical core only")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("solve", "compile", "inspect", "evidence"):
        sub = commands.add_parser(command)
        sub.add_argument("--instance", type=Path, required=True)
        sub.add_argument("--output", type=Path, required=command == "evidence")
        if command == "solve":
            sub.add_argument("--method", choices=["classical"], default="classical")
            sub.add_argument("--solver", choices=["exact_tsp", "ortools_tsp"], default="ortools_tsp")
            sub.add_argument("--scale", type=int, default=1000)
            sub.add_argument("--timeout-s", type=float, default=1.0)
        if command == "compile":
            sub.add_argument("--penalty", type=float)
            sub.add_argument("--scale", type=float, default=1.0)
        if command == "inspect":
            sub.add_argument("--qubo", type=Path, required=True)
            sub.add_argument("--bits", required=True, help="MSB-first displayed binary string; rightmost is x0")
    args = parser.parse_args(argv)
    try:
        problem = TspProblem()
        instance = problem.validate_input(read_json(args.instance))
        if args.command == "evidence":
            payload = generate_evidence(instance, args.output)
            print(json.dumps(payload, indent=2, allow_nan=False))
            return 0
        if args.command == "solve":
            handle = problem.build_classical_model(instance, args.solver)
            result = exact_solve(handle.instance) if handle.solver_id == "exact_tsp" else ortools_solve(
                handle.instance, scale=args.scale, timeout_s=args.timeout_s
            )
            payload = result.model_dump()
        elif args.command == "compile":
            payload = compile_qubo(instance, penalty=args.penalty, scale=args.scale).model_dump()
        else:
            qubo = QuboArtifact.model_validate(read_json(args.qubo))
            verify_artifact(instance, qubo)
            bits = bits_from_display(args.bits, len(qubo.variables))
            decoded = decode_assignment(instance, bits)
            payload = {"bits_index_order": bits, "energy": qubo.energy(bits), **decoded.model_dump(),
                       "original_objective": evaluate_original_objective(instance, decoded.assignment) if decoded.assignment else None}
        if args.output:
            write_json(args.output, payload)
        else:
            print(json.dumps(payload, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, OverflowError, ValidationError) as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
