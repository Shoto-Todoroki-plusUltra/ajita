"""B1: single-slot classroom events; no calendar or recurrence inference."""

import hashlib
import json
from itertools import combinations
from typing import Annotated, Literal

from pydantic import Field, model_validator

from quantum_workload_studio.models.tsp import StrictModel, ValidationReport, Violation

Id = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^\S+$")]
Count = Annotated[int, Field(ge=0, le=1_000_000)]


class Room(StrictModel):
    id: Id
    capacity: Count


class Slot(StrictModel):
    id: Id
    label: Annotated[str, Field(min_length=1, max_length=128)]
    order: Count


class Course(StrictModel):
    id: Id
    lecturer_id: Id
    cohort_ids: Annotated[list[Id], Field(max_length=50)]
    enrollment: Annotated[int, Field(ge=1, le=1_000_000)]


class Placement(StrictModel):
    course_id: Id
    room_id: Id
    slot_id: Id


class Preference(Placement):
    penalty: Count


class TimetableInstance(StrictModel):
    schema_version: Literal[1]
    kind: Literal["timetable"]
    instance_id: Id
    rooms: Annotated[list[Room], Field(min_length=1, max_length=20)]
    slots: Annotated[list[Slot], Field(min_length=1, max_length=40)]
    lecturer_ids: Annotated[list[Id], Field(min_length=1, max_length=50)]
    cohort_ids: Annotated[list[Id], Field(max_length=50)]
    courses: Annotated[list[Course], Field(min_length=1, max_length=50)]
    preferences: Annotated[list[Preference], Field(max_length=20_000)] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def version(cls, value):
        if isinstance(value, dict) and type(value.get("schema_version")) is not int:
            raise ValueError("schema_version must be integer 1")
        return value

    @model_validator(mode="after")
    def references(self):
        for values in [
            [r.id for r in self.rooms],
            [s.id for s in self.slots],
            [s.order for s in self.slots],
            self.lecturer_ids,
            self.cohort_ids,
            [c.id for c in self.courses],
            [(p.course_id, p.room_id, p.slot_id) for p in self.preferences],
        ]:
            if len(set(values)) != len(values):
                raise ValueError("IDs, slot orders and preference triples must be unique")
        for c in self.courses:
            if c.lecturer_id not in self.lecturer_ids:
                raise ValueError("unknown lecturer")
            if len(set(c.cohort_ids)) != len(c.cohort_ids) or not set(c.cohort_ids) <= set(
                self.cohort_ids
            ):
                raise ValueError("duplicate or unknown cohort reference")
        for p in self.preferences:
            if (
                p.course_id not in {c.id for c in self.courses}
                or p.room_id not in {r.id for r in self.rooms}
                or p.slot_id not in {s.id for s in self.slots}
            ):
                raise ValueError("unknown preference reference")
        if len(self.courses) * len(self.rooms) * len(self.slots) > 20_000:
            raise ValueError("B1 model supports at most 20000 assignment cells")
        return self

    def instance_hash(self):
        data = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()


class TimetableAssignment(StrictModel):
    assignments: Annotated[list[Placement], Field(max_length=256)]


def validate_assignment(
    instance: TimetableInstance, assignment: TimetableAssignment
) -> ValidationReport:
    """Original-domain checks, independent of binary mappings and solver constraints."""
    courses = {c.id: c for c in instance.courses}
    rooms = {r.id: r for r in instance.rooms}
    slots = {s.id for s in instance.slots}
    violations = []

    def add(code, ids, message):
        violations.append(Violation(code=code, entity_ids=ids, message=message))

    for c in instance.courses:
        count = sum(p.course_id == c.id for p in assignment.assignments)
        if count != 1:
            add("course_count", [c.id], f"expected one event, got {count}")
    known = []
    for p in assignment.assignments:
        if p.course_id not in courses or p.room_id not in rooms or p.slot_id not in slots:
            add(
                "unknown_reference",
                [p.course_id, p.room_id, p.slot_id],
                "unknown assignment reference",
            )
            continue
        known.append(p)
        if rooms[p.room_id].capacity < courses[p.course_id].enrollment:
            add("capacity", [p.course_id, p.room_id], "enrollment exceeds room capacity")
    for a, b in combinations(known, 2):
        if a.slot_id != b.slot_id:
            continue
        ca, cb = courses[a.course_id], courses[b.course_id]
        ids = [a.course_id, b.course_id, a.slot_id]
        if a.room_id == b.room_id:
            add("room_conflict", ids, "room used twice in one slot")
        if ca.lecturer_id == cb.lecturer_id:
            add("lecturer_conflict", ids, "lecturer has simultaneous events")
        if set(ca.cohort_ids) & set(cb.cohort_ids):
            add("cohort_conflict", ids, "cohort has simultaneous events")
    return ValidationReport(checked=True, feasible=not violations, violations=violations)


def original_objective(instance: TimetableInstance, assignment: TimetableAssignment) -> int:
    if not validate_assignment(instance, assignment).feasible:
        raise ValueError("original preference objective requires a feasible timetable")
    costs = {(p.course_id, p.room_id, p.slot_id): p.penalty for p in instance.preferences}
    return sum(costs.get((p.course_id, p.room_id, p.slot_id), 0) for p in assignment.assignments)
