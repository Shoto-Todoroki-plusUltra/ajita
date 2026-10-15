"""Explicit Qiskit operator boundary, cross-checked against independent 1A energy."""
import math

from quantum_workload_studio.qubo.basis import to_ising_basis
from quantum_workload_studio.qubo.tsp import bits_from_display, bits_from_integer, direct_evaluate


def sparse_operator(qubo):
    from qiskit.quantum_info import SparsePauliOp

    basis = to_ising_basis(qubo)
    n = len(qubo.variables)
    terms = []
    for index, coefficient in enumerate(basis.linear):
        if coefficient:
            label = ["I"]*n
            label[n-1-index] = "Z"
            terms.append(("".join(label), coefficient))
    for i, j, coefficient in basis.quadratic:
        if coefficient:
            label = ["I"]*n
            label[n-1-i] = label[n-1-j] = "Z"
            terms.append(("".join(label), coefficient))
    operator = SparsePauliOp.from_list(terms or [("I"*n, 0.0)]).simplify(atol=0, rtol=0)
    return operator, basis.offset


def normalize_counts(counts, logical_to_classical):
    """Map displayed classical register bits to logical variable bits.

    Transpilation maintains classical wiring. Do not apply its physical layout a
    second time to the counts. This function requires one complete named register.
    """
    n = len(logical_to_classical)
    if sorted(logical_to_classical) != list(range(n)):
        raise ValueError("measurement map must be a complete permutation")
    normalized = {}
    for displayed, count in counts.items():
        if type(count) is not int or count <= 0:
            raise ValueError("sample counts must be positive integers")
        classical_bits = bits_from_display(displayed, n)
        logical_bits = [classical_bits[c] for c in logical_to_classical]
        logical_display = "".join(map(str, reversed(logical_bits)))
        normalized[logical_display] = normalized.get(logical_display, 0)+count
    return normalized


def verify_basis_operator(instance, qubo):
    from qiskit.quantum_info import Statevector

    if len(qubo.variables) != 9:
        raise ValueError("1B exhaustive operator certificate requires nine variables")
    operator, offset = sparse_operator(qubo)
    records = []
    for integer in range(512):
        bits = bits_from_integer(integer, 9)
        value = complex(Statevector.from_int(integer, 512).expectation_value(operator))
        reference = direct_evaluate(instance, bits, qubo.penalties[0].weight).energy*qubo.scale
        total = value.real+offset
        if abs(value.imag) > 1e-10 or not math.isclose(total, reference, rel_tol=1e-12, abs_tol=1e-10):
            raise ValueError(f"Qiskit basis energy mismatch at {integer}")
        records.append({"integer": integer, "display": format(integer, "09b"),
                        "operator_expectation": value.real, "offset": offset,
                        "total_energy": total, "independent_reference": reference,
                        "absolute_error": abs(total-reference)})
    return {"basis_states": records, "offset": offset,
            "pauli_terms": [[label, float(value.real)] for label, value in operator.to_list()],
            "max_absolute_error": max(r["absolute_error"] for r in records),
            "relative_tolerance": 1e-12, "absolute_tolerance": 1e-10,
            "bit_order": "logical i -> qubit i -> Pauli character n-1-i; displayed rightmost bit is x0"}
