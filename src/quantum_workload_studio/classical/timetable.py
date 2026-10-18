"""Independent enumeration oracle and first-class native CP-SAT baseline."""

import math
import time
from itertools import product
from typing import Literal

from pydantic import Field

from quantum_workload_studio.models.timetable import (
    Placement,
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.models.tsp import StrictModel, ValidationReport


class TimetableResult(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["timetable"] = "timetable"
    method: Literal["classical"] = "classical"
    objective_unit: Literal["preference_penalty"] = "preference_penalty"
    instance_hash: str
    solver_id: Literal["cp_sat", "enumeration"]
    native_status: str
    assignment: TimetableAssignment | None
    validation: ValidationReport
    objective: int | None
    best_objective_bound: float | None
    proven_optimal: bool
    proven_infeasible: bool
    solver_elapsed_s: float
    enumerated_assignments: int | None = None
    options: dict = Field(default_factory=dict)


def result(instance, solver, status, assignment, bound, elapsed, **kwargs):
    validation = (
        validate_assignment(instance, assignment)
        if assignment is not None
        else ValidationReport(checked=False, feasible=None, violations=[])
    )
    if assignment is not None and not validation.feasible:
        raise RuntimeError("solver candidate failed independent original-domain validation")
    objective = original_objective(instance, assignment) if assignment is not None else None
    return TimetableResult(
        instance_hash=instance.instance_hash(),
        solver_id=solver,
        native_status=status,
        assignment=assignment,
        validation=validation,
        objective=objective,
        best_objective_bound=bound,
        proven_optimal=status == "OPTIMAL",
        proven_infeasible=status == "INFEASIBLE",
        solver_elapsed_s=elapsed,
        **kwargs,
    )


def enumerate_solve(instance: TimetableInstance, *, limit=65_536) -> TimetableResult:
    """Enumerate original room/slot choices, including capacity-invalid choices.

    Deliberately does not consume the QUBO variable map or CP-SAT model.
    """
    start = time.monotonic()
    choices = [(r.id, s.id) for r in instance.rooms for s in instance.slots]
    count = len(choices) ** len(instance.courses)
    if type(limit) is not int or not 1 <= limit <= 65_536 or count > limit:
        raise ValueError("enumeration supports at most 65536 original assignments")
    best, cost = None, None
    for selected in product(choices, repeat=len(instance.courses)):
        candidate = TimetableAssignment(
            assignments=[
                Placement(course_id=c.id, room_id=r, slot_id=s)
                for c, (r, s) in zip(instance.courses, selected)
            ]
        )
        if validate_assignment(instance, candidate).feasible:
            value = original_objective(instance, candidate)
            if cost is None or value < cost:
                best, cost = candidate, value
    return result(
        instance,
        "enumeration",
        "OPTIMAL" if best else "INFEASIBLE",
        best,
        float(cost) if cost is not None else None,
        time.monotonic() - start,
        enumerated_assignments=count,
    )


def cp_sat_solve(instance: TimetableInstance, *, timeout_s=10.0, seed=1729) -> TimetableResult:
    if isinstance(timeout_s, bool) or not math.isfinite(timeout_s) or not 0 < timeout_s <= 60:
        raise ValueError("timeout_s must be finite in (0,60]")
    if type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("seed must be integer in [0,2^31)")
    from ortools.sat.python import cp_model

    start = time.monotonic()
    model = cp_model.CpModel()
    variables = []
    for c in instance.courses:
        group = []
        for r in instance.rooms:
            if r.capacity < c.enrollment:
                continue
            for s in instance.slots:
                x = model.new_bool_var(f"x_{len(variables)}")
                variables.append((c, r, s, x))
                group.append(x)
        model.add_exactly_one(group)
    # Independently grouped resource constraints (not QUBO conflict-pair generation).
    for slot in instance.slots:
        for room in instance.rooms:
            model.add_at_most_one(
                [x for c, r, s, x in variables if s.id == slot.id and r.id == room.id]
            )
        for lecturer in instance.lecturer_ids:
            model.add_at_most_one(
                [x for c, r, s, x in variables if s.id == slot.id and c.lecturer_id == lecturer]
            )
        for cohort in instance.cohort_ids:
            model.add_at_most_one(
                [x for c, r, s, x in variables if s.id == slot.id and cohort in c.cohort_ids]
            )
    costs = {(p.course_id, p.room_id, p.slot_id): p.penalty for p in instance.preferences}
    model.minimize(sum(costs.get((c.id, r.id, s.id), 0) * x for c, r, s, x in variables))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(timeout_s)
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    status = solver.solve(model)
    name = solver.status_name(status)
    assignment = None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignment = TimetableAssignment(
            assignments=[
                Placement(course_id=c.id, room_id=r.id, slot_id=s.id)
                for c, r, s, x in variables
                if solver.value(x)
            ]
        )
    # Infeasible/model-invalid responses have no meaningful finite optimization bound.
    bound = (
        solver.best_objective_bound
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.UNKNOWN)
        else None
    )
    answer = result(
        instance,
        "cp_sat",
        name,
        assignment,
        bound,
        time.monotonic() - start,
        options={
            "timeout_s": float(timeout_s),
            "seed": seed,
            "num_search_workers": 1,
            "native_wall_time_s": solver.wall_time,
        },
    )
    if assignment is not None and answer.objective != solver.objective_value:
        raise RuntimeError("native objective disagrees with original objective")
    return answer
