"""Domain validation is independent of solvers and QUBO coefficients."""

import hashlib
import json
import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Number = Annotated[float, Field(allow_inf_nan=False)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Identifier = Annotated[str, Field(min_length=1, max_length=128)]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_assignment=True)


class MatrixInput(StrictModel):
    kind: Literal["matrix"]
    distances: Annotated[list[Annotated[list[Nonnegative], Field(min_length=4, max_length=200)]], Field(min_length=4, max_length=200)]


class Point(StrictModel):
    city_id: Identifier
    x: Number
    y: Number


class CoordinatesInput(StrictModel):
    kind: Literal["coordinates"]
    metric: Literal["euclidean_2d"]
    points: Annotated[list[Point], Field(min_length=4, max_length=200)]


class TspInstance(StrictModel):
    schema_version: Literal[1]
    kind: Literal["tsp"]
    instance_id: Identifier
    city_ids: Annotated[list[Identifier], Field(min_length=4, max_length=200)]
    depot_id: Identifier
    distance_unit: Identifier
    geometry: Annotated[MatrixInput | CoordinatesInput, Field(discriminator="kind")]

    @model_validator(mode="before")
    @classmethod
    def strict_version(cls, value):
        # Literal[1] alone accepts True/1.0; portable version is a strict integer.
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("schema_version must be integer 1")
        return value

    @model_validator(mode="after")
    def validate_instance(self):
        if len(set(self.city_ids)) != len(self.city_ids):
            raise ValueError("city_ids must be unique")
        if self.depot_id not in self.city_ids:
            raise ValueError("depot must be a city")
        n = len(self.city_ids)
        if isinstance(self.geometry, MatrixInput):
            d = self.geometry.distances
            if len(d) != n or any(len(row) != n for row in d):
                raise ValueError("matrix must be square in city_ids order")
            if any(d[i][i] != 0 for i in range(n)):
                raise ValueError("matrix diagonal must be zero")
            if any(d[i][j] != d[j][i] for i in range(n) for j in range(i)):
                raise ValueError("asymmetric matrix unsupported")
        else:
            ids = [p.city_id for p in self.geometry.points]
            if len(ids) != n or set(ids) != set(self.city_ids):
                raise ValueError("exactly one point required per city")
        d = self.distance_matrix()
        if not math.isfinite(n * max(max(row) for row in d)):
            raise ValueError("tour bound overflows finite arithmetic")
        return self

    def distance_matrix(self) -> list[list[float]]:
        if isinstance(self.geometry, MatrixInput):
            return [row.copy() for row in self.geometry.distances]
        points = {p.city_id: p for p in self.geometry.points}
        ordered = [points[c] for c in self.city_ids]
        d = [[math.hypot(a.x - b.x, a.y - b.y) for b in ordered] for a in ordered]
        if any(not math.isfinite(x) for row in d for x in row):
            raise ValueError("coordinate distance overflows")
        return d

    def instance_hash(self) -> str:
        payload = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(payload.encode()).hexdigest()


class TspAssignment(StrictModel):
    # A syntactically valid candidate may still violate the original problem.
    tour: Annotated[list[Identifier], Field(max_length=201)]


class Violation(StrictModel):
    code: str
    entity_ids: list[str]
    message: str


class ValidationReport(StrictModel):
    checked: bool
    feasible: bool | None
    violations: list[Violation]


def check_hard_constraints(instance: TspInstance, assignment: TspAssignment) -> ValidationReport:
    tour = assignment.tour
    violations = []

    def add(code, ids, message):
        violations.append(Violation(code=code, entity_ids=ids, message=message))

    if len(tour) != len(instance.city_ids) + 1:
        add("route_length", [], "tour must contain n+1 city IDs")
    if not tour or tour[0] != instance.depot_id or tour[-1] != instance.depot_id:
        add("depot_closure", [instance.depot_id], "tour must start and end at depot")
    unknown = sorted(set(tour) - set(instance.city_ids))
    if unknown:
        add("unknown_city", unknown, "route references unknown cities")
    for city in instance.city_ids:
        count = tour[:-1].count(city)
        if count != 1:
            add("city_count", [city], f"expected one occurrence before closure, got {count}")
    return ValidationReport(checked=True, feasible=not violations, violations=violations)


def evaluate_original_objective(instance: TspInstance, assignment: TspAssignment) -> float:
    if not check_hard_constraints(instance, assignment).feasible:
        raise ValueError("original objective is only defined for a verified feasible route")
    d = instance.distance_matrix()
    indexes = {c: i for i, c in enumerate(instance.city_ids)}
    return math.fsum(d[indexes[a]][indexes[b]] for a, b in zip(assignment.tour, assignment.tour[1:]))
