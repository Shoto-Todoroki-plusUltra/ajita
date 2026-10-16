"""Reproduce the SDK certificate directly from the preserved 1A QUBO artifact."""
import hashlib
import json
from pathlib import Path

from quantum_workload_studio.models.tsp import TspInstance
from quantum_workload_studio.qubo.tsp import QuboArtifact, verify_artifact
from quantum_workload_studio.execution.operator import verify_basis_operator

base = Path("evidence/checkpoint1a")
instance = TspInstance.model_validate_json((base/"instance.json").read_text())
qubo = QuboArtifact.model_validate_json((base/"qubo.json").read_text())
verify_artifact(instance, qubo)
certificate = verify_basis_operator(instance, qubo)
certificate["input_qubo_sha256"] = hashlib.sha256((base/"qubo.json").read_bytes()).hexdigest()
Path("evidence/checkpoint1b/operator-basis.json").write_text(json.dumps(certificate,indent=2)+'\n')
print("512 basis states verified; maximum absolute error:",certificate["max_absolute_error"])
