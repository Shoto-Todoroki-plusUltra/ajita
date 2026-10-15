"""Exhaustive permutation oracle and a bounded OR-Tools routing baseline."""

import itertools
import math
import time
from typing import Literal

from pydantic import Field

from quantum_workload_studio.models.tsp import (
    Nonnegative, StrictModel, TspAssignment, TspInstance, ValidationReport,
    check_hard_constraints, evaluate_original_objective,
)


class RouteCost(StrictModel):
    assignment: TspAssignment
    objective: Nonnegative


class SolveResult(StrictModel):
    schema_version: Literal[1] = 1
    instance_id: str
    instance_hash: str
    method: Literal["classical"] = "classical"
    solver_id: Literal["exact_tsp", "ortools_tsp"]
    solver_status: str
    outcome: Literal["feasible", "no_solution"]
    assignment: TspAssignment | None
    validation: ValidationReport
    objective: Nonnegative | None
    objective_unit: str
    proven_optimal: bool
    tied_optima: list[TspAssignment] = Field(default_factory=list)
    enumerated_routes: list[RouteCost] = Field(default_factory=list)
    solve_seconds: Nonnegative
    options: dict


def exact_solve(instance: TspInstance) -> SolveResult:
    """Enumerate original routes; no binary encoding or QUBO imports."""
    if len(instance.city_ids) > 8:
        raise ValueError("exact oracle limited to 8 cities")
    start = time.perf_counter()
    others = [c for c in instance.city_ids if c != instance.depot_id]
    table = []
    for permutation in itertools.permutations(others):
        assignment = TspAssignment(tour=[instance.depot_id, *permutation, instance.depot_id])
        table.append(RouteCost(assignment=assignment, objective=evaluate_original_objective(instance, assignment)))
    optimum = min(row.objective for row in table)
    # Exact float ties only; no approximate equality asserted as an optimum tie.
    ties = [row.assignment for row in table if row.objective == optimum]
    return SolveResult(
        instance_id=instance.instance_id, instance_hash=instance.instance_hash(),
        solver_id="exact_tsp", solver_status="enumeration_complete", outcome="feasible",
        assignment=ties[0], validation=check_hard_constraints(instance, ties[0]),
        objective=optimum, objective_unit=instance.distance_unit, proven_optimal=True,
        tied_optima=ties, enumerated_routes=table, solve_seconds=time.perf_counter()-start,
        options={"depot_fixed": True, "tie_break": "input_city_order", "seed": None},
    )


def ortools_solve(instance: TspInstance, *, scale: int = 1000, timeout_s: float = 1.0) -> SolveResult:
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    if type(scale) is not int or not 1 <= scale <= 10**9:
        raise ValueError("scale must be integer in [1, 1e9]")
    if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or not 0.001 <= timeout_s <= 60:
        raise ValueError("timeout_s must be finite in [0.001, 60]")
    n = len(instance.city_ids)
    d = instance.distance_matrix()
    if n * max(max(row) for row in d) * scale >= 2**62:
        raise ValueError("scaled route may overflow guarded int64 range")
    costs = [[round(x * scale) for x in row] for row in d]
    manager = pywrapcp.RoutingIndexManager(n, 1, instance.city_ids.index(instance.depot_id))
    routing = pywrapcp.RoutingModel(manager)
    callback = routing.RegisterTransitCallback(
        lambda a, b: costs[manager.IndexToNode(a)][manager.IndexToNode(b)]
    )
    routing.SetArcCostEvaluatorOfAllVehicles(callback)
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT
    params.time_limit.FromMilliseconds(max(1, int(timeout_s * 1000)))
    start = time.perf_counter()
    solution = routing.SolveWithParameters(params)
    elapsed = time.perf_counter() - start
    assignment = None
    if solution is not None:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            route.append(instance.city_ids[manager.IndexToNode(index)])
            index = solution.Value(routing.NextVar(index))
        route.append(instance.depot_id)
        assignment = TspAssignment(tour=route)
    validation = check_hard_constraints(instance, assignment) if assignment else ValidationReport(
        checked=False, feasible=None, violations=[]
    )
    if assignment and not validation.feasible:
        raise ValueError("OR-Tools returned invalid original route")
    return SolveResult(
        instance_id=instance.instance_id, instance_hash=instance.instance_hash(),
        solver_id="ortools_tsp", solver_status=str(routing.status()),
        outcome="feasible" if assignment else "no_solution", assignment=assignment,
        validation=validation,
        objective=evaluate_original_objective(instance, assignment) if assignment else None,
        objective_unit=instance.distance_unit, proven_optimal=False, solve_seconds=elapsed,
        options={"scale": scale, "rounding": "nearest_ties_to_even", "timeout_s": timeout_s,
                 "strategy": "PATH_CHEAPEST_ARC", "search": "GREEDY_DESCENT", "seed": None,
                 "integer_objective": solution.ObjectiveValue() if solution else None,
                 "tour_rounding_error_bound": n/(2*scale)},
    )
