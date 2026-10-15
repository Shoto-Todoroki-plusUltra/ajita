import pytest

pytest.importorskip("qiskit")
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import Statevector

from quantum_workload_studio.execution.operator import normalize_counts, sparse_operator, verify_basis_operator
from quantum_workload_studio.qubo.tsp import bits_from_display, compile_qubo, direct_evaluate


@pytest.fixture(scope="module")
def certificate():
    import json
    from pathlib import Path
    from quantum_workload_studio.models.tsp import TspInstance
    instance = TspInstance.model_validate_json((Path(__file__).parents[2]/"examples/tsp/four_city.json").read_text())
    qubo = compile_qubo(instance)
    return verify_basis_operator(instance, qubo)


@pytest.mark.parametrize("integer", range(512))
def test_all_qiskit_basis_energies(certificate, integer):
    row = certificate["basis_states"][integer]
    assert row["total_energy"] == pytest.approx(row["independent_reference"], rel=1e-12, abs=1e-10)


def test_sign_offset_and_label_order(instance):
    qubo = compile_qubo(instance)
    operator, offset = sparse_operator(qubo)
    zero = Statevector.from_label("000000000").expectation_value(operator).real
    one = Statevector.from_label("000000001").expectation_value(operator).real
    assert zero+offset == 96
    assert one+offset == 65
    assert one-zero == -31  # catches sign, variable zero and omitted offset errors
    assert "IIIIIIIIZ" in operator.paulis.to_labels()
    assert "ZIIIIIIII" in operator.paulis.to_labels()


@pytest.mark.parametrize("backend", ["statevector", "aer"])
def test_permuted_measurements_and_physical_layout(instance, backend):
    if backend == "aer":
        pytest.importorskip("qiskit_aer")
        from qiskit_aer.primitives import SamplerV2
        sampler = SamplerV2(seed=91, options={"backend_options": {"method": "statevector", "max_parallel_threads": 1}})
    else:
        sampler = StatevectorSampler(seed=91)
    logical_display = "010100001"  # non-palindromic feasible A-B-D-C-A
    logical_bits = bits_from_display(logical_display, 9)
    wire_map = [2, 0, 8, 1, 7, 3, 6, 4, 5]
    circuit = QuantumCircuit(9, 9)
    for i, bit in enumerate(logical_bits):
        if bit:
            circuit.x(i)
    circuit.measure(range(9), wire_map)
    layout = list(reversed(range(9)))
    compiled = transpile(circuit, basis_gates=["u", "cx"], initial_layout=layout,
                         coupling_map=[[i, j] for i in range(9) for j in range(9) if abs(i-j) == 1],
                         seed_transpiler=91, optimization_level=1)
    raw = sampler.run([compiled], shots=32).result()[0].data.c.get_counts()
    assert normalize_counts(raw, wire_map) == {logical_display: 32}
    # Explicitly test operator layout as well as classical readout wiring.
    operator, offset = sparse_operator(compile_qubo(instance))
    physical_bits = [0]*9
    for logical, physical in enumerate(layout):
        physical_bits[physical] = logical_bits[logical]
    physical_state = Statevector.from_label("".join(map(str, reversed(physical_bits))))
    assert physical_state.expectation_value(operator.apply_layout(layout)).real+offset == 6


@pytest.mark.parametrize("counts,map_", [({"010": 1}, [0, 0, 1]), ({"0 1": 2}, [0, 1, 2]),
                                       ({"000": -1}, [0, 1, 2]), ({"000": True}, [0, 1, 2])])
def test_bad_measurement_counts(counts, map_):
    with pytest.raises(ValueError):
        normalize_counts(counts, map_)
