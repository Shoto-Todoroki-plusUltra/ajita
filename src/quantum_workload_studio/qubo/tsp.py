"""Reduced city-by-position TSP QUBO and strict versioned portable format."""

import math
from collections import defaultdict
from itertools import combinations
from typing import Annotated, Literal

from pydantic import Field, model_validator

from quantum_workload_studio.models.tsp import (
    Identifier, Nonnegative, Number, StrictModel, TspAssignment, TspInstance,
    ValidationReport, Violation, check_hard_constraints,
)


def validate_bits(bits: list[int], size: int) -> None:
    if type(bits) is not list or len(bits) != size or any(type(x) is not int or x not in (0, 1) for x in bits):
        raise ValueError(f"assignment must be a list of exactly {size} integer binary values")


def bits_from_integer(value: int, size: int) -> list[int]:
    if type(value) is not int or type(size) is not int or not 1 <= size <= 49 or not 0 <= value < 2**size:
        raise ValueError("integer assignment outside encoding range")
    return [(value >> i) & 1 for i in range(size)]


def bits_from_display(value: str, size: int) -> list[int]:
    if type(value) is not str or len(value) != size or set(value) - {"0", "1"}:
        raise ValueError("display string must have exactly n binary characters")
    return [int(x) for x in reversed(value)]


class DomainRef(StrictModel):
    city_id: Identifier
    position: Annotated[int, Field(ge=0, le=7)]


class Variable(StrictModel):
    index: Annotated[int, Field(ge=0, le=48)]
    name: Identifier
    domain_ref: DomainRef


class Term(StrictModel):
    i: Annotated[int, Field(ge=0, le=48)]
    j: Annotated[int, Field(ge=0, le=48)]
    coefficient: Number


class FixedVariable(StrictModel):
    domain_ref: DomainRef
    value: Annotated[int, Field(ge=0, le=1)]


class DecodeMap(StrictModel):
    city_ids: Annotated[list[Identifier], Field(min_length=4, max_length=8)]
    depot_id: Identifier
    active_indices: list[int]
    fixed_variables: list[FixedVariable]
    auxiliary_variables: list[Identifier] = Field(max_length=0)


class Penalty(StrictModel):
    constraint_family: Literal["one_city_per_position", "one_position_per_city"]
    weight: Nonnegative
    adequacy_status: Literal["sufficient_bound", "unproven_experiment"]
    bound_basis: Literal["A > n*d_max; nonnegative cost and integer residuals"]
    feasible_cost_upper_bound: Nonnegative


class Provenance(StrictModel):
    implementation: Literal["quantum_workload_studio.explicit_tsp"]
    version: Literal["0.1.0"]
    converter_sequence: list[str] = Field(max_length=0)


class QuboArtifact(StrictModel):
    schema_version: Literal[1]
    convention: Literal["upper_triangular"]
    sense: Literal["minimize"]
    variables: Annotated[list[Variable], Field(min_length=9, max_length=49)]
    terms: Annotated[list[Term], Field(max_length=1225)]
    offset: Number
    energy_unit: Identifier
    scale: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    source_instance_hash: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    encoding_id: Literal["tsp_position_depot_fixed"]
    encoding_version: Literal[1]
    penalties: Annotated[list[Penalty], Field(min_length=2, max_length=2)]
    decode_map: DecodeMap
    provenance: Provenance

    @model_validator(mode="before")
    @classmethod
    def strict_versions(cls, data):
        if isinstance(data, dict) and any(type(data.get(k)) is not int for k in ("schema_version", "encoding_version")):
            raise ValueError("format and encoding versions must be integer 1")
        return data

    @model_validator(mode="after")
    def canonical(self):
        ids, depot = self.decode_map.city_ids, self.decode_map.depot_id
        if len(ids) != len(set(ids)) or depot not in ids:
            raise ValueError("invalid decode-map city/depot IDs")
        active = [c for c in ids if c != depot]
        m = len(active)
        expected = [(c, t) for c in active for t in range(1, m+1)]
        if len(self.variables) != m*m or self.decode_map.active_indices != list(range(m*m)):
            raise ValueError("invalid active dimensions/order")
        if [v.index for v in self.variables] != list(range(m*m)):
            raise ValueError("variable indices must be contiguous in order")
        if len({v.name for v in self.variables}) != m*m:
            raise ValueError("duplicate variable name")
        if [(v.domain_ref.city_id, v.domain_ref.position) for v in self.variables] != expected:
            raise ValueError("variable domain references do not match registered decoder")
        fixed = [(f.domain_ref.city_id, f.domain_ref.position, f.value) for f in self.decode_map.fixed_variables]
        expected_fixed = [(c, t, int(c == depot and t == 0)) for c in ids for t in range(m+1) if c == depot or t == 0]
        if fixed != expected_fixed:
            raise ValueError("fixed depot map mismatch")
        pairs = [(t.i, t.j) for t in self.terms]
        if pairs != sorted(set(pairs)) or any(i > j or j >= m*m for i, j in pairs):
            raise ValueError("terms must be unique upper-triangular, ordered and in range")
        if [p.constraint_family for p in self.penalties] != ["one_city_per_position", "one_position_per_city"]:
            raise ValueError("invalid penalty families/order")
        a, b = self.penalties
        if a.weight != b.weight or a.feasible_cost_upper_bound != b.feasible_cost_upper_bound:
            raise ValueError("registered encoder requires equal weights and bound")
        status = "sufficient_bound" if a.weight > a.feasible_cost_upper_bound else "unproven_experiment"
        if any(p.adequacy_status != status for p in self.penalties):
            raise ValueError("penalty adequacy label contradicts bound")
        return self

    def energy(self, bits: list[int]) -> float:
        validate_bits(bits, len(self.variables))
        return math.fsum([self.offset, *(t.coefficient*bits[t.i]*bits[t.j] for t in self.terms)])


def compile_qubo(instance: TspInstance, *, penalty: float | None = None, scale: float = 1.0) -> QuboArtifact:
    n = len(instance.city_ids)
    if n > 8:
        raise ValueError("QUBO compilation limited to 8 cities")
    upper = n * max(max(row) for row in instance.distance_matrix())
    if penalty is None:
        penalty = upper + max(1.0, upper)
    for name, value in [("penalty", penalty), ("scale", scale)]:
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (name == "scale" and value == 0):
            raise ValueError(f"invalid finite {name}")
    active = [c for c in instance.city_ids if c != instance.depot_id]
    m = n-1
    variables = [Variable(index=i*m+t-1, name=f"x_{i}_{t}", domain_ref=DomainRef(city_id=c, position=t))
                 for i, c in enumerate(active) for t in range(1, n)]
    q = defaultdict(float)

    def add(i, j, value):
        q[min(i, j), max(i, j)] += value

    # Expand the two one-hot constraint families independently of direct evaluation.
    groups = [[i*m+t for t in range(m)] for i in range(m)]
    groups += [[i*m+t for i in range(m)] for t in range(m)]
    for group in groups:
        for i in group:
            add(i, i, -penalty)
        for i, j in combinations(group, 2):
            add(i, j, 2*penalty)
    d = instance.distance_matrix()
    city_index = {c: i for i, c in enumerate(instance.city_ids)}
    depot = city_index[instance.depot_id]
    for i, c in enumerate(active):
        add(i*m, i*m, d[depot][city_index[c]])
        add(i*m+m-1, i*m+m-1, d[city_index[c]][depot])
        for j, other in enumerate(active):
            for t in range(m-1):
                add(i*m+t, j*m+t+1, d[city_index[c]][city_index[other]])
    return QuboArtifact(
        schema_version=1, convention="upper_triangular", sense="minimize", variables=variables,
        terms=[Term(i=i, j=j, coefficient=v*scale) for (i, j), v in sorted(q.items()) if v != 0],
        offset=2*m*penalty*scale, energy_unit=instance.distance_unit, scale=scale,
        source_instance_hash=instance.instance_hash(), encoding_id="tsp_position_depot_fixed", encoding_version=1,
        penalties=[Penalty(constraint_family=family, weight=penalty,
                           adequacy_status="sufficient_bound" if penalty > upper else "unproven_experiment",
                           bound_basis="A > n*d_max; nonnegative cost and integer residuals",
                           feasible_cost_upper_bound=upper)
                   for family in ("one_city_per_position", "one_position_per_city")],
        decode_map=DecodeMap(city_ids=instance.city_ids.copy(), depot_id=instance.depot_id,
                             active_indices=list(range(m*m)), auxiliary_variables=[],
                             fixed_variables=[FixedVariable(domain_ref=DomainRef(city_id=c, position=t),
                                                            value=int(c == instance.depot_id and t == 0))
                                              for c in instance.city_ids for t in range(n)
                                              if c == instance.depot_id or t == 0]),
        provenance=Provenance(implementation="quantum_workload_studio.explicit_tsp", version="0.1.0", converter_sequence=[]),
    )


def verify_artifact(instance: TspInstance, artifact: QuboArtifact) -> None:
    """A schema-valid imported polynomial is not automatically this instance's encoding."""
    expected = compile_qubo(instance, penalty=artifact.penalties[0].weight, scale=artifact.scale)
    if artifact != expected:
        raise ValueError("artifact does not match original instance and registered encoding")


class DirectEvaluation(StrictModel):
    cost: Nonnegative
    city_residuals: list[int]
    position_residuals: list[int]
    city_penalties: list[Nonnegative]
    position_penalties: list[Nonnegative]
    energy: Number


def direct_evaluate(instance: TspInstance, bits: list[int], penalty: float) -> DirectEvaluation:
    """Unexpanded residuals/cost: does not consult QUBO terms or the builder."""
    cities = [c for c in instance.city_ids if c != instance.depot_id]
    m = len(cities)
    validate_bits(bits, m*m)
    if type(penalty) not in (int, float) or not math.isfinite(penalty) or penalty < 0:
        raise ValueError("invalid penalty")
    y = [bits[i*m:(i+1)*m] for i in range(m)]
    index = {c: i for i, c in enumerate(instance.city_ids)}
    d = instance.distance_matrix()
    depot = index[instance.depot_id]
    cost_terms = [d[depot][index[c]]*y[i][0] + d[index[c]][depot]*y[i][-1] for i, c in enumerate(cities)]
    for t in range(m-1):
        for i, city in enumerate(cities):
            for j, other in enumerate(cities):
                cost_terms.append(d[index[city]][index[other]]*y[i][t]*y[j][t+1])
    cost = math.fsum(cost_terms)
    rows = [1-sum(row) for row in y]
    cols = [1-sum(y[i][t] for i in range(m)) for t in range(m)]
    rp, cp = [penalty*r*r for r in rows], [penalty*c*c for c in cols]
    return DirectEvaluation(cost=cost, city_residuals=rows, position_residuals=cols,
                            city_penalties=rp, position_penalties=cp, energy=math.fsum([cost, *rp, *cp]))


class DecodeOutcome(StrictModel):
    assignment: TspAssignment | None
    validation: ValidationReport


def decode_assignment(instance: TspInstance, bits: list[int]) -> DecodeOutcome:
    cities = [c for c in instance.city_ids if c != instance.depot_id]
    m = len(cities)
    validate_bits(bits, m*m)
    violations = []
    for i, city in enumerate(cities):
        count = sum(bits[i*m:(i+1)*m])
        if count != 1:
            violations.append(Violation(code="missing_city" if count == 0 else "duplicate_city",
                                        entity_ids=[city], message=f"city selected {count} times"))
    route = [instance.depot_id]
    for t in range(m):
        selected = [city for i, city in enumerate(cities) if bits[i*m+t]]
        if len(selected) != 1:
            violations.append(Violation(code="empty_position" if not selected else "multiple_cities_at_position",
                                        entity_ids=[str(t+1)], message=f"position selects {len(selected)} cities"))
        else:
            route.append(selected[0])
    if violations:
        return DecodeOutcome(assignment=None, validation=ValidationReport(checked=True, feasible=False, violations=violations))
    route.append(instance.depot_id)
    assignment = TspAssignment(tour=route)
    return DecodeOutcome(assignment=assignment, validation=check_hard_constraints(instance, assignment))


def encode_assignment(instance: TspInstance, assignment: TspAssignment) -> list[int]:
    if not check_hard_constraints(instance, assignment).feasible:
        raise ValueError("cannot encode infeasible route")
    cities = [c for c in instance.city_ids if c != instance.depot_id]
    return [int(assignment.tour[t] == city) for city in cities for t in range(1, len(instance.city_ids))]
