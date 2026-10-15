"""Reproducible checkpoint proof artifacts, not a performance benchmark."""

import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from quantum_workload_studio.classical.tsp import exact_solve, ortools_solve
from quantum_workload_studio.models.tsp import TspInstance, evaluate_original_objective
from quantum_workload_studio.qubo.basis import to_ising_basis
from quantum_workload_studio.qubo.tsp import (
    QuboArtifact, bits_from_integer, compile_qubo, decode_assignment, direct_evaluate, encode_assignment,
)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def generate_evidence(instance: TspInstance, output: Path) -> dict:
    if len(instance.city_ids) != 4:
        raise ValueError("checkpoint evidence requires exactly four cities (512 assignments)")
    output.mkdir(parents=True, exist_ok=True)
    qubo = compile_qubo(instance)
    ising = to_ising_basis(qubo)
    exact = exact_solve(instance)
    baseline = ortools_solve(instance)
    records = []
    for integer in range(512):
        bits = bits_from_integer(integer, 9)
        direct = direct_evaluate(instance, bits, qubo.penalties[0].weight)
        decoded = decode_assignment(instance, bits)
        energy = qubo.energy(bits)
        basis_energy = ising.energy(bits)
        # Integer fixture compares exactly; floats use explicitly recorded tolerance.
        if not (math.isclose(energy, direct.energy, rel_tol=1e-12, abs_tol=1e-10)
                and math.isclose(energy, basis_energy, rel_tol=1e-12, abs_tol=1e-10)):
            raise ValueError(f"energy mismatch for assignment {integer}")
        objective = None
        if decoded.assignment is not None:
            if encode_assignment(instance, decoded.assignment) != bits:
                raise ValueError("route round trip failed")
            objective = evaluate_original_objective(instance, decoded.assignment)
        records.append({"integer": integer, "display_msb_first": format(integer, "09b"),
                        "bits_index_order": bits, "direct": direct.model_dump(),
                        "qubo_energy": energy, "ising_basis_energy": basis_energy,
                        "feasible": decoded.validation.feasible,
                        "assignment": decoded.assignment.model_dump() if decoded.assignment else None,
                        "violations": [v.model_dump() for v in decoded.validation.violations],
                        "original_objective": objective})
    feasible = [r for r in records if r["feasible"]]
    if len(feasible) != 6:
        raise ValueError("four-city one-hot feasible count mismatch")
    if {tuple(r["assignment"]["tour"]) for r in feasible} != {tuple(r.assignment.tour) for r in exact.enumerated_routes}:
        raise ValueError("decoded feasible routes disagree with independent route oracle")
    best_energy = min(r["qubo_energy"] for r in records)
    if any(not r["feasible"] for r in records if r["qubo_energy"] == best_energy):
        raise ValueError("default-penalty global minimizer is infeasible")
    weak = compile_qubo(instance, penalty=0)
    invalid = decode_assignment(instance, [0]*9)
    zero_cost = weak.energy([0]*9)
    d = instance.distance_matrix()
    lower = 4*min(d[i][j] for i in range(4) for j in range(4) if i != j)
    root = Path(__file__).resolve().parents[2]
    source_hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((root / "src").rglob("*.py"))}
    lock = root / "requirements/macos-arm64-py312.lock"
    if not lock.exists():
        raise ValueError("generate the lockfile before recording reproducibility evidence")
    environment = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "architecture": platform.machine(), "macos": platform.mac_ver()[0],
        "packages": {name: importlib.metadata.version(name) for name in ["pydantic", "ortools", "pytest", "pip-tools"]},
        "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(), "source_sha256": source_hashes,
        "quantum_execution": False, "peak_memory_bytes": None, "seed": None,
        "note": "Deterministic enumeration; OR-Tools deterministic strategies, no random sampler; timings are single-run measurements, not benchmarks.",
    }
    summary = {"schema_version": 1, "instance_hash": instance.instance_hash(), "assignments": 512,
               "feasible": len(feasible), "infeasible": 512-len(feasible),
               "exact_optimum": exact.objective, "tied_optima": len(exact.tied_optima),
               "original_lower_bound": lower, "lower_bound_attained": exact.objective == lower,
               "qubo_global_minimum": best_energy, "offset": qubo.offset,
               "penalty": qubo.penalties[0].weight, "min_infeasible_energy": min(r["qubo_energy"] for r in records if not r["feasible"]),
               "energy_comparison": {"relative_tolerance": 1e-12, "absolute_tolerance": 1e-10,
                                     "all_exactly_equal": all(r["qubo_energy"] == r["direct"]["energy"] == r["ising_basis_energy"] for r in records)},
               "weak_penalty_example": {"penalty": 0, "bits": [0]*9, "energy": zero_cost,
                                        "feasible": invalid.validation.feasible,
                                        "below_feasible_optimum": zero_cost < exact.objective,
                                        "violations": [v.model_dump() for v in invalid.validation.violations]},
               "ortools_original_objective": baseline.objective, "quantum_advantage_demonstrated": False}
    payloads = {"instance.json": instance.model_dump(),
                "distances.json": {"city_ids": instance.city_ids, "unit": instance.distance_unit, "distances": d},
                "qubo.json": qubo.model_dump(),
                "ising_basis.json": {"offset": ising.offset, "linear": list(ising.linear),
                                     "quadratic": [list(term) for term in ising.quadratic],
                                     "spin_convention": "z_i=1-2*x_i", "scale": qubo.scale,
                                     "note": "Classical polynomial only; no quantum execution"},
                "routes.json": exact.model_dump(), "ortools.json": baseline.model_dump(),
                "assignments.json": records, "summary.json": summary, "environment.json": environment,
                "tsp.schema.json": TspInstance.model_json_schema(), "qubo.schema.json": QuboArtifact.model_json_schema()}
    for filename, payload in payloads.items():
        write_json(output / filename, payload)
    with (output / "assignments.csv").open("w", newline="") as stream:
        columns = ["integer", "display_msb_first", "bits_index_order", "direct_cost", "direct_energy", "city_residuals", "position_residuals",
                   "city_penalties", "position_penalties", "qubo_energy", "ising_basis_energy", "feasible", "tour", "violations", "original_objective"]
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow({"integer": row["integer"], "display_msb_first": row["display_msb_first"],
                             "bits_index_order": json.dumps(row["bits_index_order"]), "direct_cost": row["direct"]["cost"],
                             "direct_energy": row["direct"]["energy"],
                             **{k: json.dumps(row["direct"][k]) for k in ["city_residuals", "position_residuals", "city_penalties", "position_penalties"]},
                             "qubo_energy": row["qubo_energy"], "ising_basis_energy": row["ising_basis_energy"],
                             "feasible": row["feasible"], "tour": json.dumps(row["assignment"]),
                             "violations": json.dumps(row["violations"]), "original_objective": row["original_objective"]})
    files = [*payloads, "assignments.csv"]
    write_json(output / "manifest.json", {"schema_version": 1, "sha256": {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in sorted(files)}})
    return summary
