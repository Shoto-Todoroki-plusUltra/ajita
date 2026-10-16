"""Time-boxed optional published Mapper cross-check; never used by QAOA.

Run in the separately resolved Mapper environment. Same reduced variables and
explicit A; no library TSP model, automatic penalties, extra/slack variables.
"""
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_addon_opt_mapper.problems import OptimizationProblem
from qiskit_addon_opt_mapper.converters import OptimizationProblemToQubo
from qiskit_addon_opt_mapper.translators import to_ising

from quantum_workload_studio.models.tsp import TspInstance
from quantum_workload_studio.qubo.tsp import QuboArtifact, bits_from_integer, decode_assignment, direct_evaluate, verify_artifact

start = time.monotonic()
base = Path("evidence/checkpoint1a")
instance = TspInstance.model_validate_json((base/"instance.json").read_text())
reference = QuboArtifact.model_validate_json((base/"qubo.json").read_text())
verify_artifact(instance, reference)
assert len(reference.variables) == 9
problem = OptimizationProblem("reduced_tsp_explicit_penalty")
for variable in reference.variables:
    problem.binary_var(name=variable.name)
active = [c for c in instance.city_ids if c != instance.depot_id]
d = instance.distance_matrix()
index = {c:i for i,c in enumerate(instance.city_ids)}
depot = index[instance.depot_id]
linear, quadratic = {}, {}
for i, city in enumerate(active):
    linear[i*3] = d[depot][index[city]]
    linear[i*3+2] = d[index[city]][depot]
    for j, other in enumerate(active):
        for t in range(2):
            pair = (i*3+t, j*3+t+1)
            quadratic[pair] = d[index[city]][index[other]]
problem.minimize(linear=linear, quadratic=quadratic)
for i in range(3):
    problem.linear_constraint(linear={i*3+t:1 for t in range(3)}, sense="EQ", rhs=1, name=f"city_{i}")
for t in range(3):
    problem.linear_constraint(linear={i*3+t:1 for i in range(3)}, sense="EQ", rhs=1, name=f"position_{t}")
converter = OptimizationProblemToQubo(penalty=16)
if not converter.is_compatible(problem):
    raise ValueError(converter.get_compatibility_msg(problem))
converted = converter.convert(problem)
assert [v.name for v in converted.variables] == [v.name for v in reference.variables]
assert converted.objective.constant == reference.offset
canonical = {}
for i, value in converted.objective.linear.to_dict().items():
    canonical[i,i] = canonical.get((i,i),0)+float(value)
for (i,j), value in converted.objective.quadratic.to_dict().items():
    pair = (min(i,j), max(i,j))
    canonical[pair] = canonical.get(pair,0)+float(value)
canonical = {pair:value for pair,value in canonical.items() if value != 0}
assert canonical == {(t.i,t.j):t.coefficient for t in reference.terms}
operator, offset = to_ising(converted)
records = []
for integer in range(512):
    if time.monotonic()-start > 30:
        raise TimeoutError("Mapper cross-check exceeded 30-second compute budget")
    bits = bits_from_integer(integer, 9)
    direct = direct_evaluate(instance, bits, 16).energy
    value = float(converted.objective.evaluate(np.array(bits)))
    operator_value = float(Statevector.from_int(integer, 512).expectation_value(operator).real)+offset
    assert abs(value-direct) <= 1e-10
    assert abs(operator_value-direct) <= 1e-10
    interpreted = converter.interpret(np.array(bits)).tolist()
    assert interpreted == bits
    feasible = decode_assignment(instance, [int(x) for x in interpreted]).validation.feasible
    records.append({"integer": integer, "reference": direct, "mapper_energy": value,
                    "mapper_operator_plus_offset": operator_value, "feasible": feasible})
result = {"status": "passed", "mapper_release": importlib.metadata.version("qiskit-addon-opt-mapper"),
          "explicit_penalty": 16, "canonical_coefficients_and_offset_equal":True,
          "variable_order": [v.name for v in converted.variables],
          "variable_count": len(converted.variables), "slack_variables": 0,
          "records": records, "max_absolute_energy_error": max(abs(r["reference"]-r["mapper_energy"]) for r in records),
          "feasible_count": sum(r["feasible"] for r in records), "offset": float(offset),
          "elapsed_s": time.monotonic()-start, "compute_budget_s":30,
          "input_qubo_sha256":hashlib.sha256((base/"qubo.json").read_bytes()).hexdigest(),
          "packages":{d.metadata["Name"]:d.version for d in importlib.metadata.distributions()},
          "note":"Cross-check only; direct core still executes QAOA. No CPLEX/Gurobi job invoked."}
Path("evidence/checkpoint1b/mapper-crosscheck.json").write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ["status","mapper_release","variable_count","feasible_count","max_absolute_energy_error","elapsed_s"]})
