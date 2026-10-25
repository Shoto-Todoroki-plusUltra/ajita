"""Mapping-only tests: SDK basis expectations, never Sampler or QAOA execution."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantum_workload_studio.execution.mapping_certificate import certify_fixtures
from quantum_workload_studio.execution.research_mapping import (
    B1ResearchInput,
    TspResearchInput,
    artifact_digest,
    check_research_options,
    decode_b1_readouts,
    prepare_b1,
    prepare_b1_sampling_boundary,
    prepare_tsp,
)
from quantum_workload_studio.models.timetable import TimetableInstance
from quantum_workload_studio.models.tsp import TspInstance
from quantum_workload_studio.qubo.timetable import compile_qubo as compile_b1
from quantum_workload_studio.qubo.timetable import direct_energy
from quantum_workload_studio.qubo.tsp import compile_qubo as compile_tsp

ROOT = Path(__file__).resolve().parents[2]


def b1(name="B0"):
    return TimetableInstance.model_validate_json(
        (ROOT / f"examples/research_mapping/{name}.json").read_text()
    )


def request(instance, *, penalty=None, scale=1.0, normalization="ising_l1"):
    tsp = isinstance(instance, TspInstance)
    q = (compile_tsp if tsp else compile_b1)(instance, penalty=penalty, scale=scale)
    cls = TspResearchInput if tsp else B1ResearchInput
    return cls(
        schema_version=1,
        artifact=q,
        artifact_sha256=artifact_digest(q),
        normalization=normalization,
    )


@pytest.fixture(scope="module")
def certificate():
    pytest.importorskip("qiskit")
    return certify_fixtures(ROOT)


@pytest.mark.parametrize("row", range(3897))
def test_all_planned_basis_rows(certificate, row):
    # Exhaustive full rows, not randomized/selected basis states.
    index = row
    for cert in certificate["certificates"]:
        if index < len(cert["basis_states"]):
            data = cert["basis_states"][index]
            assert (
                data["direct_energy"] == data["expanded_energy"] == data["classical_ising_energy"]
            )
            if data["sdk_total_energy"] is not None:
                assert data["sdk_total_energy"] == pytest.approx(
                    data["direct_energy"], abs=1e-10, rel=1e-12
                )
                assert data["normalized_sdk_total_energy"] == pytest.approx(
                    data["direct_energy"] / cert["normalized_mapping"]["normalization_divisor"],
                    abs=1e-10,
                    rel=1e-12,
                )
            return
        index -= len(cert["basis_states"])
    pytest.fail("missing certificate row")


@pytest.mark.parametrize("scale", [0.25, 1.0, 7.0])
@pytest.mark.parametrize("name", ["tiny", "ties", "shared-slot", "capacity"])
def test_accepted_b1_cases_scale_and_offsets(name, scale):
    pytest.importorskip("qiskit")
    from qiskit.quantum_info import Statevector

    data = json.loads((ROOT / "examples/timetable/tiny.json").read_text())
    if name == "ties":
        data["preferences"] = []
    if name == "shared-slot":
        data["slots"] = data["slots"][:1]
        data["preferences"] = []
    if name == "capacity":
        data["rooms"][0]["capacity"] = 0
    instance = TimetableInstance.model_validate(data)
    q, m = prepare_b1(instance, request(instance, scale=scale, normalization="none"))
    if not q.variables:
        assert m.basis.offset == q.offset == 2 * scale
        with pytest.raises(ValueError, match="zero-variable"):
            m.sparse_operator()
        return
    op, offset = m.sparse_operator()
    assert offset == m.basis.offset
    for integer in range(2 ** len(q.variables)):
        bits = [(integer >> i) & 1 for i in range(len(q.variables))]
        reference = direct_energy(instance, q, bits)
        assert Statevector.from_int(integer, 2 ** len(q.variables)).expectation_value(
            op
        ).real + offset == pytest.approx(reference, abs=1e-10)
    if name == "tiny":
        assert q.offset == 12 * scale
        assert m.basis.offset == 12 * scale  # 12 - 18/2 + 36/4
        assert Statevector.from_int(1, 16).expectation_value(op).real + offset == 6 * scale
        assert "IIIZ" in op.paulis.to_labels()


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("normalization", "auto"),
        ("artifact_sha256", "0" * 64),
    ],
)
def test_strict_request_versions_and_digest(field, value):
    r = request(b1())
    d = r.model_dump()
    d[field] = value
    with pytest.raises(ValueError):
        prepare_b1(b1(), B1ResearchInput.model_validate(d))


@pytest.mark.parametrize(
    "change", ["coefficient", "offset", "hash", "version", "map", "provenance"]
)
def test_reject_mutated_or_stale_even_with_new_digest(change):
    r = request(b1())
    d = r.model_dump()
    if change == "coefficient":
        d["artifact"]["terms"][0]["coefficient"] += 1
    if change == "offset":
        d["artifact"]["offset"] += 1
    if change == "hash":
        d["artifact"]["source_instance_hash"] = "0" * 64
    if change == "version":
        d["artifact"]["encoding_version"] = True
    if change == "map":
        d["artifact"]["variables"][0]["slot_id"] = "missing"
    if change == "provenance":
        d["artifact"]["provenance"] = "arbitrary converter"
    with pytest.raises(ValueError):
        parsed = B1ResearchInput.model_validate(d)
        parsed.artifact_sha256 = artifact_digest(parsed.artifact)
        prepare_b1(b1(), parsed)


def test_mutable_instance_and_domain_mismatch(instance):
    r = request(b1())
    altered = b1()
    altered.preferences[0].penalty = 99
    with pytest.raises(ValueError):
        prepare_b1(altered, r)
    r.artifact.offset += 1
    with pytest.raises(ValueError):
        prepare_b1(b1(), r)
    with pytest.raises(ValidationError):
        TspResearchInput.model_validate(request(b1()).model_dump())
    with pytest.raises(ValidationError):
        B1ResearchInput.model_validate(request(instance).model_dump())
    t = request(instance)
    t.artifact.terms[0].coefficient += 1
    t.artifact_sha256 = artifact_digest(t.artifact)
    with pytest.raises(ValueError):
        prepare_tsp(instance, t)


def test_research_sizes_and_zero_operator(instance):
    from quantum_workload_studio.models.tsp import TspInstance

    d = instance.model_dump()
    d["city_ids"] = list("ABCDE")
    d["geometry"] = {
        "kind": "matrix",
        "distances": [[0 if i == j else 1 for i in range(5)] for j in range(5)],
    }
    large = TspInstance.model_validate(d)
    with pytest.raises(ValueError, match="9 active"):
        prepare_tsp(large, request(large))
    d = instance.model_dump()
    d["geometry"]["distances"] = [[0] * 4 for _ in range(4)]
    zero = TspInstance.model_validate(d)
    with pytest.raises(ValueError, match="nonzero"):
        prepare_tsp(zero, request(zero, penalty=0))
    data = b1().model_dump()
    data["slots"] = [{"id": f"s{k}", "label": str(k), "order": k} for k in range(5)]
    data["preferences"] = []
    large = TimetableInstance.model_validate(data)
    with pytest.raises(ValueError, match="9 active"):
        prepare_b1(large, request(large))


def test_research_option_guards_and_preflight():
    from quantum_workload_studio.execution.local import LocalOptions

    opts = LocalOptions(timeout_s=20.0, memory_limit_mb=512)
    for update in [
        {"reps": 2},
        {"shots": 257},
        {"max_evaluations": 17},
        {"timeout_s": 21.0},
        {"memory_limit_mb": 1024},
        {"backend": "aer"},
    ]:
        with pytest.raises(ValueError):
            check_research_options(opts.model_copy(update=update))
    prepared = prepare_b1_sampling_boundary(b1(), request(b1()), opts)
    assert prepared["execution_authorized"] is False
    with pytest.raises(ValueError):
        prepare_b1_sampling_boundary(b1("N1"), request(b1("N1"), normalization="none"), opts)
    with pytest.raises(ValueError, match="modeled"):
        prepare_b1_sampling_boundary(
            b1(), request(b1()), opts.model_copy(update={"memory_limit_mb": 64})
        )


def test_supplied_readouts_not_experiments():
    i = b1("B1")
    r = request(i)
    # Explicit mathematical readout fixtures; no measurements are made here.
    result = decode_b1_readouts(i, r, {"00100001": 3, "00000000": 6, "bad": 1}, list(range(8)))
    assert (
        result["raw_shots"] == 10 and result["feasible_shots"] == 3 and result["invalid_shots"] == 7
    )
    assert result["best_feasible"]["bits_index_order"] == [1, 0, 0, 0, 0, 1, 0, 0]
    assert result["best_feasible"]["original_objective"] == 1
    assert "supplied readout" in result["source"]
    assert decode_b1_readouts(i, r, {}, list(range(8)))["feasible_fraction"] is None
    assert decode_b1_readouts(i, r, {"00000000": 4}, list(range(8)))["best_feasible"] is None
    for counts, map_ in [
        ({"0": True}, list(range(8))),
        ({"0": 4097}, list(range(8))),
        ({}, [0] * 8),
        ({}, [False, *range(1, 8)]),
    ]:
        with pytest.raises(ValueError):
            decode_b1_readouts(i, r, counts, map_)


def test_nonidentity_physical_and_classical_mapping():
    pytest.importorskip("qiskit")
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Statevector

    i = b1("B1")
    q, m = prepare_b1(i, request(i, normalization="none"))
    bits = [1, 0, 0, 0, 0, 1, 0, 0]
    physical_layout = [7, 6, 5, 4, 3, 2, 1, 0]
    classical_map = [2, 0, 7, 1, 6, 3, 5, 4]
    circuit = QuantumCircuit(8, 8)
    for index, bit in enumerate(bits):
        if bit:
            circuit.x(index)
    circuit.measure(range(8), classical_map)
    compiled = transpile(
        circuit,
        initial_layout=physical_layout,
        coupling_map=[[a, b] for a in range(8) for b in range(8) if abs(a - b) == 1],
        basis_gates=["u", "cx"],
        optimization_level=1,
        seed_transpiler=7,
    )
    # Deterministic statevector algebra on preparation circuit, no sampler/measurement execution.
    state = Statevector.from_instruction(compiled.remove_final_measurements(inplace=False))
    layout = compiled.layout.final_index_layout()
    assert layout != list(range(8))
    op, offset = m.sparse_operator()
    assert (
        state.expectation_value(op.apply_layout(compiled.layout)).real + offset
        == pytest.approx(q.energy(bits))
        == 1
    )
    physical_integer = max(range(256), key=lambda k: abs(state.data[k]))
    classical = [0] * 8
    for instruction in compiled.data:
        if instruction.operation.name == "measure":
            physical = compiled.find_bit(instruction.qubits[0]).index
            c = compiled.find_bit(instruction.clbits[0]).index
            classical[c] = (physical_integer >> physical) & 1
    displayed = "".join(map(str, reversed(classical)))
    decoded = decode_b1_readouts(i, request(i), {displayed: 1}, classical_map)
    assert decoded["best_feasible"]["bits_index_order"] == bits
    # One-hot non-palindrome stays infeasible, despite valid SDK format.
    assert (
        decode_b1_readouts(b1(), request(b1()), {"0001": 1}, [0, 1, 2, 3])["best_feasible"] is None
    )


def test_tsp_parent_default_and_explicit_payload_without_worker(instance, monkeypatch):
    from quantum_workload_studio.execution import local

    opts = local.LocalOptions(timeout_s=20.0, memory_limit_mb=512)

    class ReachedBoundary(Exception):
        pass

    seen = []

    def capture(payload, *args, **kwargs):
        seen.append(payload)
        raise ReachedBoundary

    monkeypatch.setattr(local, "supervise", capture)
    with pytest.raises(ReachedBoundary):
        local.run_local(instance, opts)
    assert set(seen[-1]) == {"instance", "options"}  # original default payload unchanged
    r = request(instance, penalty=64)
    with pytest.raises(ReachedBoundary):
        local.run_local(instance, opts, research=r)
    assert seen[-1]["research"] == r.model_dump()
    r.artifact.offset += 1
    with pytest.raises(ValueError):
        local.run_local(instance, opts, research=r)
    assert len(seen) == 2  # stale artifact rejected before process admission


def test_classical_imports_no_quantum():
    code = "from quantum_workload_studio.execution import research_mapping; from quantum_workload_studio.api.app import app; import sys; assert not any(n.startswith(('qiskit','scipy','numpy')) for n in sys.modules); print('classical imports clean')"
    answer = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert answer.returncode == 0, answer.stderr


def test_worker_resolves_exact_explicit_artifact_without_running_qaoa(instance):
    pytest.importorskip("qiskit")
    from qiskit.quantum_info import Statevector

    from quantum_workload_studio.execution.local import LocalOptions
    from quantum_workload_studio.execution.operator import sparse_operator
    from quantum_workload_studio.execution.research_mapping import resolve_tsp_worker_input

    options = LocalOptions(timeout_s=20.0, memory_limit_mb=512)
    legacy = compile_tsp(instance)
    old_op, old_offset = sparse_operator(legacy)
    r = request(instance, normalization="none")
    artifact, operator, offset, divisor, metadata = resolve_tsp_worker_input(
        instance, options, r.model_dump()
    )
    assert artifact == legacy and divisor == 1
    assert operator.to_list() == old_op.to_list() and offset == old_offset
    r = request(instance, penalty=64, normalization="ising_l1")
    artifact, operator, offset, divisor, metadata = resolve_tsp_worker_input(
        instance, options, r.model_dump()
    )
    for i in range(512):
        bits = [(i >> j) & 1 for j in range(9)]
        assert Statevector.from_int(i, 512).expectation_value(
            operator
        ).real + offset == pytest.approx(artifact.energy(bits) / divisor, abs=1e-10)
    r.artifact.source_instance_hash = "0" * 64
    with pytest.raises(ValueError):
        resolve_tsp_worker_input(instance, options, r.model_dump())
