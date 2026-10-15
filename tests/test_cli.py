import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from quantum_workload_studio.cli import main, read_json
from quantum_workload_studio.domains.tsp import TspProblem
from quantum_workload_studio.evidence import generate_evidence
from quantum_workload_studio.qubo.tsp import compile_qubo

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/tsp/four_city.json"


def test_cli_solve_compile_inspect(tmp_path, capsys):
    base = ["--instance", str(FIXTURE)]
    for solver in ["exact_tsp", "ortools_tsp"]:
        assert main(["solve", *base, "--solver", solver]) == 0
        result = json.loads(capsys.readouterr().out)
        assert result["objective"] == 4 and result["validation"]["feasible"]
    qubo_file = tmp_path / "qubo.json"
    assert main(["compile", *base, "--output", str(qubo_file)]) == 0
    assert main(["inspect", *base, "--qubo", str(qubo_file), "--bits", "100010001"]) == 0
    valid = json.loads(capsys.readouterr().out)
    assert valid["validation"]["feasible"] and valid["original_objective"] == 4
    assert main(["inspect", *base, "--qubo", str(qubo_file), "--bits", "000000000"]) == 0
    invalid = json.loads(capsys.readouterr().out)
    assert not invalid["validation"]["feasible"] and invalid["original_objective"] is None
    assert main(["inspect", *base, "--qubo", str(qubo_file), "--bits", "xx"]) == 2
    assert "error" in json.loads(capsys.readouterr().err)
    data = json.loads(qubo_file.read_text())
    data["terms"][0]["coefficient"] += 1
    qubo_file.write_text(json.dumps(data))
    assert main(["inspect", *base, "--qubo", str(qubo_file), "--bits", "100010001"]) == 2
    assert "does not match" in capsys.readouterr().err


def test_reject_duplicate_and_invalid_json(tmp_path, capsys):
    path = tmp_path / "bad.json"
    for content in ['{"schema_version":1,"schema_version":1}', '{"cost":NaN}', '{}', 'not json']:
        path.write_text(content)
        assert main(["solve", "--instance", str(path)]) == 2
        assert capsys.readouterr().err
    path.write_bytes(b" "*(2*1024*1024+1))
    assert main(["solve", "--instance", str(path)]) == 2
    assert "exceeds" in capsys.readouterr().err


def test_subprocess_cli_excludes_quantum():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run([sys.executable, "-m", "quantum_workload_studio.cli", "solve",
                             "--instance", str(FIXTURE), "--solver", "exact_tsp"],
                            env=env, text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["objective"] == 4
    unsupported = subprocess.run([sys.executable, "-m", "quantum_workload_studio.cli", "solve",
                                  "--instance", str(FIXTURE), "--method", "quantum_local"],
                                 env=env, text=True, capture_output=True)
    assert unsupported.returncode == 2


def test_evidence_artifacts(instance, tmp_path):
    summary = generate_evidence(instance, tmp_path / "first")
    again = generate_evidence(instance, tmp_path / "second")
    assert summary == again
    assert summary["assignments"] == 512
    assert summary["feasible"] == 6 and summary["infeasible"] == 506
    assert summary["exact_optimum"] == summary["qubo_global_minimum"] == 4
    assert summary["lower_bound_attained"] and summary["energy_comparison"]["all_exactly_equal"]
    first, second = tmp_path / "first", tmp_path / "second"
    for name in ["instance.json", "qubo.json", "assignments.json", "assignments.csv", "summary.json"]:
        assert (first/name).read_bytes() == (second/name).read_bytes()
    rows = json.loads((first/"assignments.json").read_text())
    assert len(rows) == 512 and len({r["integer"] for r in rows}) == 512
    assert sum(r["feasible"] for r in rows) == 6
    with (first/"assignments.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 512
    assert b"\r" not in (first/"assignments.csv").read_bytes()
    manifest = json.loads((first/"manifest.json").read_text())
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((first/name).read_bytes()).hexdigest() == digest


def test_domain_protocol_verifies_decoded_candidate(instance):
    domain = TspProblem()
    validated = domain.validate_input(instance.model_dump())
    assert domain.summarize_instance(validated)["city_count"] == 4
    assert domain.build_classical_model(validated, "exact_tsp").instance == instance
    qubo = domain.to_qubo(validated)
    decoded = domain.decode_assignment(validated, [1,0,0,0,1,0,0,0,1])
    assert domain.check_hard_constraints(validated, decoded.assignment).feasible
    assert domain.evaluate_original_objective(validated, decoded.assignment) == qubo.energy([1,0,0,0,1,0,0,0,1]) == 4
