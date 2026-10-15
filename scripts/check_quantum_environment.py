"""Executed compatibility smoke; local-only primitives, no provider services."""
import importlib.metadata
import json
import psutil
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import BaseSamplerV2, StatevectorSampler
from qiskit_aer.primitives import SamplerV2 as AerSamplerV2

circuit = QuantumCircuit(3, 3)
circuit.x(0)
circuit.measure([0, 1, 2], [2, 0, 1])
compiled = transpile(circuit, basis_gates=["u", "cx"], coupling_map=[[0, 1], [1, 0], [1, 2], [2, 1]],
                     initial_layout=[2, 0, 1], seed_transpiler=7, optimization_level=1)
results = {}
for name, sampler in [("statevector", StatevectorSampler(seed=7)),
                       ("aer", AerSamplerV2(seed=7, options={"backend_options": {"method": "statevector", "max_parallel_threads": 1}}))]:
    assert isinstance(sampler, BaseSamplerV2)
    counts = sampler.run([compiled], shots=32).result()[0].data.c.get_counts()
    assert counts == {"100": 32}, counts
    results[name] = counts
print(json.dumps({"packages": {n: importlib.metadata.version(n) for n in ["qiskit", "qiskit-aer", "scipy", "psutil"]},
                  "non_palindromic_permuted_measurement_counts": results,
                  "initial_layout": [2, 0, 1], "logical_to_classical": [2, 0, 1],
                  "available_memory_bytes": psutil.virtual_memory().available}, indent=2))
