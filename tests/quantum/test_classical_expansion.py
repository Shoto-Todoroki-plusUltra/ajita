"""Small independent original-objective and floating-encoding regressions."""
import random
from functools import lru_cache

import pytest

from quantum_workload_studio.classical.tsp import exact_solve, ortools_solve
from quantum_workload_studio.models.tsp import TspInstance
from quantum_workload_studio.qubo.tsp import bits_from_integer, compile_qubo, direct_evaluate


@pytest.mark.parametrize("n", [4, 5, 6])
def test_original_oracle_against_independent_dynamic_program(n):
    rng = random.Random(81+n)
    d = [[0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            d[i][j] = d[j][i] = rng.randint(1, 20)
    @lru_cache(None)
    def path(last, remaining):
        if not remaining:
            return d[last][0]
        return min(d[last][j]+path(j, remaining & ~(1 << j)) for j in range(1, n) if remaining & (1 << j))
    reference = path(0, sum(1 << j for j in range(1, n)))
    instance = TspInstance(schema_version=1, kind="tsp", instance_id=f"seeded_{n}",
                           city_ids=[str(i) for i in range(n)], depot_id="0", distance_unit="synthetic_cost",
                           geometry={"kind": "matrix", "distances": d})
    exact = exact_solve(instance)
    assert exact.objective == reference
    assert ortools_solve(instance).objective >= reference


def test_five_city_encoded_energy_random_assignments():
    d = [[0 if i == j else abs(i-j)+1 for j in range(5)] for i in range(5)]
    instance = TspInstance(schema_version=1, kind="tsp", instance_id="five", city_ids=list("ABCDE"),
                           depot_id="A", distance_unit="synthetic_cost", geometry={"kind": "matrix", "distances": d})
    qubo = compile_qubo(instance)
    rng = random.Random(313)
    for _ in range(256):
        bits = bits_from_integer(rng.randrange(2**16), 16)
        assert qubo.energy(bits) == direct_evaluate(instance, bits, qubo.penalties[0].weight).energy


def test_float_cost_rounding_reported_separately(instance):
    data = instance.model_dump()
    data["geometry"]["distances"] = [[x/7 for x in row] for row in data["geometry"]["distances"]]
    scaled = TspInstance.model_validate(data)
    result = ortools_solve(scaled, scale=1)
    tour = result.assignment.tour
    index = {c:i for i,c in enumerate(scaled.city_ids)}
    independently_scored = sum(scaled.geometry.distances[index[a]][index[b]] for a,b in zip(tour,tour[1:]))
    assert result.objective == pytest.approx(independently_scored)
    assert result.options["tour_rounding_error_bound"] == 2
    assert not result.proven_optimal
