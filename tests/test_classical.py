import copy
import itertools
import math

import pytest
from pydantic import ValidationError

from quantum_workload_studio.classical.tsp import exact_solve, ortools_solve
from quantum_workload_studio.models.tsp import (
    TspAssignment, TspInstance, check_hard_constraints, evaluate_original_objective,
)


def test_independent_six_routes(instance):
    # Hand-tabulated original costs; no encoder or solver helpers in expectations.
    expected = {("B", "C", "D"): 4, ("B", "D", "C"): 6,
                ("C", "B", "D"): 6, ("C", "D", "B"): 6,
                ("D", "B", "C"): 6, ("D", "C", "B"): 4}
    result = exact_solve(instance)
    assert {tuple(r.assignment.tour[1:-1]): r.objective for r in result.enumerated_routes} == expected
    assert result.objective == 4
    # Independently establish lower bound from four positive edges >= 1.
    assert min(d for i, row in enumerate(instance.distance_matrix()) for j, d in enumerate(row) if i != j) * 4 == 4
    assert {tuple(a.tour) for a in result.tied_optima} == {("A", "B", "C", "D", "A"), ("A", "D", "C", "B", "A")}
    assert result.proven_optimal
    assert len(result.enumerated_routes) == math.factorial(3)


def test_ortools_baseline(instance):
    result = ortools_solve(instance)
    assert result.validation.feasible and result.objective == 4
    assert not result.proven_optimal
    assert result.options["integer_objective"] == 4000


@pytest.mark.parametrize("change", [
    lambda d: d.update(schema_version=True),
    lambda d: d.update(schema_version=1.0),
    lambda d: d.update(schema_version=2),
    lambda d: d.update(extra="unrecognized"),
    lambda d: d.update(depot_id="unknown"),
    lambda d: d.update(city_ids=["A", "B", "B", "D"]),
    lambda d: d["geometry"]["distances"][0].pop(),
    lambda d: d["geometry"]["distances"][0].__setitem__(0, 1),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, 7),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, -1),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, float("nan")),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, float("inf")),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, "1"),
    lambda d: d["geometry"]["distances"][0].__setitem__(1, True),
])
def test_invalid_input(instance, change):
    data = copy.deepcopy(instance.model_dump())
    change(data)
    with pytest.raises(ValidationError):
        TspInstance.model_validate(data)


@pytest.mark.parametrize("tour", [[], ["A", "B", "C", "A"], ["A", "B", "B", "D", "A"],
                                  ["B", "A", "C", "D", "B"], ["A", "B", "C", "X", "A"]])
def test_invalid_routes_not_scored(instance, tour):
    assignment = TspAssignment(tour=tour)
    assert not check_hard_constraints(instance, assignment).feasible
    with pytest.raises(ValueError, match="verified feasible"):
        evaluate_original_objective(instance, assignment)


def test_roundtrip_coordinates_and_order(instance):
    assert TspInstance.model_validate_json(instance.model_dump_json()) == instance
    assert TspInstance.model_validate_json(instance.model_dump_json()).instance_hash() == instance.instance_hash()
    data = instance.model_dump()
    data["geometry"] = {"kind": "coordinates", "metric": "euclidean_2d", "points": [
        {"city_id": c, "x": x, "y": y} for c, x, y in [("D", 0, 1), ("A", 0, 0), ("C", 1, 1), ("B", 1, 0)]
    ]}
    coordinates = TspInstance.model_validate(data)
    assert exact_solve(coordinates).objective == 4
    data["geometry"]["points"][0]["city_id"] = "B"
    with pytest.raises(ValidationError):
        TspInstance.model_validate(data)


def test_zero_distances_and_nonfirst_depot(instance):
    data = instance.model_dump()
    data["depot_id"] = "C"
    data["geometry"]["distances"] = [[0] * 4 for _ in range(4)]
    zero = TspInstance.model_validate(data)
    result = exact_solve(zero)
    assert result.objective == 0 and len(result.tied_optima) == 6
    assert result.assignment.tour[0] == "C"
    assert ortools_solve(zero).objective == 0


def test_ortools_options_and_overflow(instance):
    for options in [{"scale": True}, {"timeout_s": float("nan")}, {"timeout_s": -1}]:
        with pytest.raises(ValueError):
            ortools_solve(instance, **options)
    data = instance.model_dump()
    data["geometry"]["distances"] = [[0 if i == j else 1e17 for j in range(4)] for i in range(4)]
    with pytest.raises(ValueError, match="overflow"):
        ortools_solve(TspInstance.model_validate(data))
