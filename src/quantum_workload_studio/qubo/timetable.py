"""Bounded B1 QUBO. Pair penalties are deduplicated across conflict reasons."""

import math
from itertools import combinations
from typing import Annotated, Literal

from pydantic import Field, model_validator

from quantum_workload_studio.models.timetable import (
    Placement,
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.models.tsp import StrictModel, ValidationReport
from quantum_workload_studio.qubo.tsp import Term, validate_bits

MAX_VARIABLES = 16


class Variable(Placement):
    index: Annotated[int, Field(ge=0, le=15)]
    name: str


class TimetableQubo(StrictModel):
    schema_version: Literal[1]
    encoding_id: Literal["b1_capacity_assignment_v1"] = "b1_capacity_assignment_v1"
    encoding_version: Literal[1]
    provenance: Literal["explicit_b1_v1; no external converter"] = (
        "explicit_b1_v1; no external converter"
    )
    penalty_bound_basis: Literal["A > sum of maximum admissible preference per course"] = (
        "A > sum of maximum admissible preference per course"
    )
    convention: Literal["upper_triangular"] = "upper_triangular"
    sense: Literal["minimize"] = "minimize"
    source_instance_hash: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    variables: Annotated[list[Variable], Field(max_length=16)]
    terms: Annotated[list[Term], Field(max_length=136)]
    offset: Annotated[float, Field(allow_inf_nan=False)]
    scale: Annotated[float, Field(gt=0, le=1_000_000, allow_inf_nan=False)]
    penalty: Annotated[int, Field(ge=1, le=50_000_001)]
    soft_upper_bound: Annotated[int, Field(ge=0, le=50_000_000)]
    penalty_sufficient: bool
    bit_order: Literal["bits[i] maps variables[i]; display left-to-right is index order"] = (
        "bits[i] maps variables[i]; display left-to-right is index order"
    )
    energy_unit: Literal["scaled_preference_penalty"] = "scaled_preference_penalty"

    @model_validator(mode="before")
    @classmethod
    def version(cls, value):
        if isinstance(value, dict) and any(
            type(value.get(k)) is not int for k in ("schema_version", "encoding_version")
        ):
            raise ValueError("schema and encoding versions must be explicit integer 1")
        return value

    @model_validator(mode="after")
    def canonical(self):
        if [v.index for v in self.variables] != list(range(len(self.variables))):
            raise ValueError("variable indices must be contiguous")
        if [v.name for v in self.variables] != [f"x_{i}" for i in range(len(self.variables))]:
            raise ValueError("variable names must be canonical")
        triples = [(v.course_id, v.room_id, v.slot_id) for v in self.variables]
        if len(set(triples)) != len(triples):
            raise ValueError("duplicate domain variable")
        pairs = [(t.i, t.j) for t in self.terms]
        if pairs != sorted(set(pairs)) or any(i > j or j >= len(self.variables) for i, j in pairs):
            raise ValueError("terms must be unique upper triangular and in bounds")
        if self.penalty_sufficient != (self.penalty > self.soft_upper_bound):
            raise ValueError("inconsistent penalty bound metadata")
        return self

    def energy(self, bits: list[int]) -> float:
        validate_bits(bits, len(self.variables))
        return math.fsum(
            [self.offset, *(t.coefficient * bits[t.i] * bits[t.j] for t in self.terms)]
        )


class Decoded(StrictModel):
    assignment: TimetableAssignment
    validation: ValidationReport
    original_objective: int | None


def variable_map(instance):
    variables = []
    for course in instance.courses:
        for room in instance.rooms:
            if room.capacity >= course.enrollment:
                for slot in instance.slots:
                    if len(variables) == MAX_VARIABLES:
                        raise ValueError(
                            "unsupported_size: B1 QUBO supports at most 16 admissible variables"
                        )
                    i = len(variables)
                    variables.append(
                        Variable(
                            index=i,
                            name=f"x_{i}",
                            course_id=course.id,
                            room_id=room.id,
                            slot_id=slot.id,
                        )
                    )
    return variables


def conflict_pairs(instance, variables):
    courses = {c.id: c for c in instance.courses}
    return [
        (a.index, b.index)
        for a, b in combinations(variables, 2)
        if a.course_id != b.course_id
        and a.slot_id == b.slot_id
        and (
            a.room_id == b.room_id
            or courses[a.course_id].lecturer_id == courses[b.course_id].lecturer_id
            or bool(set(courses[a.course_id].cohort_ids) & set(courses[b.course_id].cohort_ids))
        )
    ]


def compile_qubo(
    instance: TimetableInstance, *, penalty: int | None = None, scale: float = 1.0
) -> TimetableQubo:
    variables = variable_map(instance)
    costs = {(p.course_id, p.room_id, p.slot_id): p.penalty for p in instance.preferences}
    weight = [costs.get((v.course_id, v.room_id, v.slot_id), 0) for v in variables]
    bound = sum(
        max((weight[v.index] for v in variables if v.course_id == c.id), default=0)
        for c in instance.courses
    )
    a = bound + 1 if penalty is None else penalty
    if type(a) is not int or not 1 <= a <= 50_000_001:
        raise ValueError("penalty must be integer in [1,50000001]")
    if isinstance(scale, bool) or not math.isfinite(scale) or not 0 < scale <= 1_000_000:
        raise ValueError("scale must be finite in (0,1000000]")
    coefficients = {}

    def add(i, j, value):
        coefficients[i, j] = coefficients.get((i, j), 0) + value

    for v, cost in zip(variables, weight):
        add(v.index, v.index, cost - a)
    for c in instance.courses:
        group = [v.index for v in variables if v.course_id == c.id]
        for i, j in combinations(group, 2):
            add(i, j, 2 * a)
    for i, j in conflict_pairs(instance, variables):
        add(i, j, a)
    return TimetableQubo(
        schema_version=1,
        encoding_version=1,
        source_instance_hash=instance.instance_hash(),
        variables=variables,
        terms=[
            Term(i=i, j=j, coefficient=float(value * scale))
            for (i, j), value in sorted(coefficients.items())
            if value
        ],
        offset=float(a * len(instance.courses) * scale),
        scale=float(scale),
        penalty=a,
        soft_upper_bound=bound,
        penalty_sufficient=a > bound,
    )


def direct_energy(instance, artifact, bits):
    """Unexpanded expression, deliberately independent of pair-list generation."""
    validate_bits(bits, len(artifact.variables))
    selected = [v for v in artifact.variables if bits[v.index]]
    soft = sum(
        p.penalty
        for p in instance.preferences
        for v in selected
        if (p.course_id, p.room_id, p.slot_id) == (v.course_id, v.room_id, v.slot_id)
    )
    exact = sum((sum(v.course_id == c.id for v in selected) - 1) ** 2 for c in instance.courses)
    courses = {c.id: c for c in instance.courses}
    clashes = 0
    for a, b in combinations(selected, 2):
        if a.course_id == b.course_id or a.slot_id != b.slot_id:
            continue
        ca, cb = courses[a.course_id], courses[b.course_id]
        reasons = [
            a.room_id == b.room_id,
            ca.lecturer_id == cb.lecturer_id,
            any(g in cb.cohort_ids for g in ca.cohort_ids),
        ]
        clashes += int(any(reasons))
    return artifact.scale * (soft + artifact.penalty * (exact + clashes))


def decode(instance, artifact, bits) -> Decoded:
    validate_bits(bits, len(artifact.variables))
    assignment = TimetableAssignment(
        assignments=[
            Placement(course_id=v.course_id, room_id=v.room_id, slot_id=v.slot_id)
            for v in artifact.variables
            if bits[v.index]
        ]
    )
    validation = validate_assignment(instance, assignment)
    return Decoded(
        assignment=assignment,
        validation=validation,
        original_objective=original_objective(instance, assignment)
        if validation.feasible
        else None,
    )


def encode(instance, artifact, assignment):
    if not validate_assignment(instance, assignment).feasible:
        raise ValueError("encoding requires an original-domain feasible assignment")
    keys = {(p.course_id, p.room_id, p.slot_id) for p in assignment.assignments}
    return [int((v.course_id, v.room_id, v.slot_id) in keys) for v in artifact.variables]


def verify_artifact(instance, artifact):
    expected = compile_qubo(instance, penalty=artifact.penalty, scale=artifact.scale)
    if artifact != expected:
        raise ValueError("artifact differs from canonical instance compilation")
