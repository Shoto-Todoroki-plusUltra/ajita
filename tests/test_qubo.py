import copy
import itertools
import random

import pytest
from pydantic import ValidationError

from quantum_workload_studio.classical.tsp import exact_solve
from quantum_workload_studio.models.tsp import TspAssignment, TspInstance, evaluate_original_objective
from quantum_workload_studio.qubo.basis import to_ising_basis
from quantum_workload_studio.qubo.tsp import (
    QuboArtifact, bits_from_display, bits_from_integer, compile_qubo, decode_assignment,
    direct_evaluate, encode_assignment, verify_artifact,
)


@pytest.fixture(scope="module")
def qubo_fixture():
    from pathlib import Path
    instance = TspInstance.model_validate_json((Path(__file__).parents[1] / "examples/tsp/four_city.json").read_text())
    qubo = compile_qubo(instance)
    return instance, qubo, to_ising_basis(qubo)


@pytest.mark.parametrize("integer", range(512))
def test_every_binary_assignment(qubo_fixture, integer):
    instance, qubo, ising = qubo_fixture
    bits = bits_from_integer(integer, 9)
    direct = direct_evaluate(instance, bits, 16)
    assert direct.energy == qubo.energy(bits) == ising.energy(bits)
    assert bits_from_display(format(integer, "09b"), 9) == bits
    # Permutation feasibility checked independently of both residuals and decoder.
    permutations = set()
    for order in itertools.permutations(range(3)):
        reference = [0] * 9
        for t, city in enumerate(order):
            reference[city*3+t] = 1
        permutations.add(tuple(reference))
    expected = tuple(bits) in permutations
    decoded = decode_assignment(instance, bits)
    assert decoded.validation.feasible == expected
    assert (not any(direct.city_residuals) and not any(direct.position_residuals)) == expected
    if expected:
        assert decoded.assignment is not None
        assert encode_assignment(instance, decoded.assignment) == bits
        assert evaluate_original_objective(instance, decoded.assignment) == direct.cost == direct.energy
        assert direct.energy in (4, 6)
    else:
        assert decoded.assignment is None and decoded.validation.violations
        assert direct.energy >= 16


def test_global_ground_state_and_all_routes(qubo_fixture):
    instance, qubo, _ = qubo_fixture
    valid = [(bits_from_integer(k, 9), decode_assignment(instance, bits_from_integer(k, 9))) for k in range(512)]
    feasible = [(bits, result) for bits, result in valid if result.validation.feasible]
    assert len(feasible) == 6 and len(valid)-len(feasible) == 506
    oracle = exact_solve(instance)
    assert min(qubo.energy(bits_from_integer(k, 9)) for k in range(512)) == oracle.objective == 4
    assert {tuple(d.assignment.tour) for _, d in feasible} == {tuple(r.assignment.tour) for r in oracle.enumerated_routes}
    for assignment in oracle.tied_optima:
        assert qubo.energy(encode_assignment(instance, assignment)) == 4


def test_coefficients_offset_and_scale(qubo_fixture):
    instance, qubo, _ = qubo_fixture
    terms = {(t.i, t.j): t.coefficient for t in qubo.terms}
    assert qubo.offset == 96 and qubo.penalties[0].weight == 16
    assert [terms[i, i] for i in range(9)] == [-31, -32, -31, -30, -32, -30, -31, -32, -31]
    assert terms[0, 1] == 32  # same city, different position
    assert terms[0, 3] == 32  # same position, different city
    assert terms[0, 4] == 1   # tour B->C, counted once
    assert qubo.energy([0]*9) == 96
    assert qubo.energy([1]+[0]*8) == 65
    scaled = compile_qubo(instance, scale=0.5)
    for k in range(512):
        bits = bits_from_integer(k, 9)
        assert scaled.energy(bits)/scaled.scale == qubo.energy(bits)
    assert bits_from_display("000000001", 9) == [1]+[0]*8


def test_weak_penalty_does_not_certify_feasibility(instance):
    weak = compile_qubo(instance, penalty=0)
    bits = [0]*9
    assert weak.energy(bits) == 0 < exact_solve(instance).objective
    assert weak.penalties[0].adequacy_status == "unproven_experiment"
    decoded = decode_assignment(instance, bits)
    assert decoded.assignment is None and not decoded.validation.feasible
    assert {v.code for v in decoded.validation.violations} == {"missing_city", "empty_position"}


@pytest.mark.parametrize("bits", [[0]*8, [0]*10, [True]+[0]*8, [0.0]*9, [2]+[0]*8, "000000001"])
def test_malformed_bits(instance, bits):
    with pytest.raises(ValueError):
        compile_qubo(instance).energy(bits)
    with pytest.raises(ValueError):
        decode_assignment(instance, bits)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(schema_version=True), lambda d: d.update(encoding_version=2),
    lambda d: d.update(convention="full_symmetric"), lambda d: d.update(encoding_id="unknown"),
    lambda d: d.update(scale=0), lambda d: d.update(offset=float("inf")),
    lambda d: d["terms"].append(d["terms"][0]),
    lambda d: d["terms"][0].update(i=1, j=0),
    lambda d: d["terms"][0].update(j=9),
    lambda d: d["variables"][1].update(index=0),
    lambda d: d["variables"][1].update(name=d["variables"][0]["name"]),
    lambda d: d["variables"][0]["domain_ref"].update(city_id="A"),
    lambda d: d["decode_map"]["fixed_variables"][0].update(value=0),
    lambda d: d["decode_map"].update(auxiliary_variables=["unrecognized"]),
    lambda d: d["penalties"][0].update(adequacy_status="unproven_experiment"),
])
def test_portable_schema_rejects_corruption(instance, mutate):
    data = copy.deepcopy(compile_qubo(instance).model_dump())
    mutate(data)
    with pytest.raises(ValidationError):
        QuboArtifact.model_validate(data)


def test_import_verification_and_roundtrip(instance):
    original = compile_qubo(instance)
    imported = QuboArtifact.model_validate_json(original.model_dump_json())
    assert imported == original
    verify_artifact(instance, imported)
    imported.terms[0].coefficient += 1
    with pytest.raises(ValueError, match="does not match"):
        verify_artifact(instance, imported)


def test_other_depot_and_float_properties(instance):
    data = instance.model_dump()
    data["depot_id"] = "C"
    data["city_ids"] = ["D", "A", "C", "B"]
    rng = random.Random(1729)
    d = [[0.0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(i):
            d[i][j] = d[j][i] = rng.random()*10
    data["geometry"]["distances"] = d
    modified = TspInstance.model_validate(data)
    qubo = compile_qubo(modified)
    ising = to_ising_basis(qubo)
    for k in range(512):
        bits = bits_from_integer(k, 9)
        reference = direct_evaluate(modified, bits, qubo.penalties[0].weight).energy
        assert qubo.energy(bits) == pytest.approx(reference, rel=1e-12, abs=1e-10)
        assert ising.energy(bits) == pytest.approx(reference, rel=1e-12, abs=1e-10)
    for row in exact_solve(modified).enumerated_routes:
        bits = encode_assignment(modified, row.assignment)
        assert decode_assignment(modified, bits).assignment == row.assignment
        assert qubo.energy(bits) == pytest.approx(row.objective, rel=1e-12, abs=1e-10)


def test_bad_parameters_and_assignment(instance):
    for options in [{"penalty": -1}, {"penalty": True}, {"scale": 0}, {"scale": float("nan")}]:
        with pytest.raises(ValueError):
            compile_qubo(instance, **options)
    with pytest.raises(ValueError):
        encode_assignment(instance, TspAssignment(tour=[]))
    for value in [-1, 512, True]:
        with pytest.raises(ValueError):
            bits_from_integer(value, 9)
