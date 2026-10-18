"""Reproduce tiny B1 mathematical evidence, not a research benchmark."""

import json
import platform
import sys
from importlib.metadata import version
from itertools import product
from pathlib import Path

from quantum_workload_studio.classical.timetable import cp_sat_solve, enumerate_solve
from quantum_workload_studio.models.timetable import TimetableInstance
from quantum_workload_studio.qubo.timetable import compile_qubo, decode, direct_energy, encode


def main():
    destination = Path("evidence/phase2")
    destination.mkdir(exist_ok=True)
    fixture = json.loads(Path("examples/timetable/tiny.json").read_text())
    summary = []
    for name in ("feasible", "shared-slot-infeasible", "capacity-infeasible", "ties"):
        data = json.loads(json.dumps(fixture))
        if name == "shared-slot-infeasible":
            data["slots"] = data["slots"][:1]
            data["preferences"] = []
        if name == "capacity-infeasible":
            data["rooms"][0]["capacity"] = 0
        if name == "ties":
            data["preferences"] = []
        instance = TimetableInstance.model_validate(data)
        oracle, cp_sat = enumerate_solve(instance), cp_sat_solve(instance)
        assert oracle.objective == cp_sat.objective
        assert oracle.proven_infeasible == cp_sat.proven_infeasible
        qubo = compile_qubo(instance)
        rows = []
        for values in product([0, 1], repeat=len(qubo.variables)):
            bits = list(values)
            decoded = decode(instance, qubo, bits)
            energy, reference = qubo.energy(bits), direct_energy(instance, qubo, bits)
            assert abs(energy - reference) <= 1e-12
            if decoded.validation.feasible:
                assert energy == decoded.original_objective
                assert encode(instance, qubo, decoded.assignment) == bits
            rows.append(
                {
                    "bits_index_order": bits,
                    "expanded_energy": energy,
                    "direct_expression_energy": reference,
                    **decoded.model_dump(),
                }
            )
        payload = {
            "instance": instance.model_dump(),
            "oracle": oracle.model_dump(),
            "cp_sat": cp_sat.model_dump(),
            "qubo": qubo.model_dump(),
            "all_binary_assignments": rows,
            "absolute_energy_tolerance": 1e-12,
        }
        (destination / f"math-{name}.json").write_text(json.dumps(payload, indent=2) + "\n")
        summary.append(
            {
                "fixture": name,
                "assignments_checked": len(rows),
                "feasible_binary_assignments": sum(r["validation"]["feasible"] for r in rows),
                "objective": oracle.objective,
                "native_status": cp_sat.native_status,
            }
        )
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": {p: version(p) for p in ("ortools", "pydantic", "fastapi", "pytest", "psutil")},
        "seed": 1729,
        "cp_sat_search_workers": 1,
        "fixtures": summary,
    }
    (destination / "mathematical-summary.json").write_text(json.dumps(environment, indent=2) + "\n")
    print(json.dumps(environment, indent=2))


if __name__ == "__main__":
    main()
