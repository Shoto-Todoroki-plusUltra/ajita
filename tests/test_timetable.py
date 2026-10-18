"""B1 domain, independent oracle, native solver and exhaustive binary checks."""

import copy
import json
import random
from itertools import product
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantum_workload_studio.classical.timetable import cp_sat_solve, enumerate_solve
from quantum_workload_studio.models.timetable import (
    TimetableAssignment,
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.qubo.timetable import (
    TimetableQubo,
    compile_qubo,
    conflict_pairs,
    decode,
    direct_energy,
    encode,
    verify_artifact,
)

FIXTURE = Path(__file__).resolve().parents[1] / "examples/timetable/tiny.json"


def fixture():
    return json.loads(FIXTURE.read_text())


def instance():
    return TimetableInstance.model_validate(fixture())


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(schema_version=True),
        lambda d: d["rooms"][0].update(capacity=True),
        lambda d: d["rooms"][0].update(capacity="30"),
        lambda d: d["courses"][0].update(enrollment=0),
        lambda d: d["courses"][0].update(lecturer_id="missing"),
        lambda d: d["courses"][0].update(cohort_ids=["G1", "G1"]),
        lambda d: d["courses"][0].update(cohort_ids=["missing"]),
        lambda d: d["rooms"].append(d["rooms"][0]),
        lambda d: d["slots"][1].update(order=0),
        lambda d: d["slots"][0].update(id=" "),
        lambda d: d["preferences"][0].update(penalty=-1),
        lambda d: d["preferences"][0].update(penalty=1.5),
        lambda d: d["preferences"][0].update(room_id="absent"),
        lambda d: d["preferences"].append(d["preferences"][0]),
        lambda d: d["courses"][0].pop("id"),
        lambda d: d.update(recurrence="weekly"),
    ],
)
def test_strict_input(change):
    d = fixture()
    change(d)
    with pytest.raises(ValidationError):
        TimetableInstance.model_validate(d)


def test_native_and_independent_optimum():
    i = instance()
    a, b = enumerate_solve(i), cp_sat_solve(i)
    assert a.objective == b.objective == 1
    assert a.proven_optimal and b.proven_optimal
    assert b.native_status == "OPTIMAL" and b.best_objective_bound == 1
    assert a.enumerated_assignments == 4
    assert b.validation.feasible
    assert cp_sat_solve(i).assignment == b.assignment


@pytest.mark.parametrize("infeasible", ["capacity", "shared_slot"])
def test_infeasibility_proofs(infeasible):
    d = fixture()
    if infeasible == "capacity":
        d["rooms"][0]["capacity"] = 0
    else:
        d["slots"] = d["slots"][:1]
        d["preferences"] = []
    i = TimetableInstance.model_validate(d)
    for solved in [enumerate_solve(i), cp_sat_solve(i)]:
        assert solved.native_status == "INFEASIBLE" and solved.proven_infeasible
        assert solved.objective is None and solved.best_objective_bound is None
        assert solved.assignment is None and not solved.proven_optimal
    q = compile_qubo(i)
    assert all(
        not decode(i, q, list(bits)).validation.feasible
        for bits in product([0, 1], repeat=len(q.variables))
    )


@pytest.mark.parametrize("scale", [0.25, 1.0, 7.0])
def test_all_tiny_binary_assignments(scale):
    i = instance()
    q = compile_qubo(i, scale=scale)
    assert len(q.variables) == 4 and q.offset == 12 * scale
    assert q.soft_upper_bound == 5 and q.penalty == 6 and q.penalty_sufficient
    # Same room, lecturer and cohort still produce only one conflict pair per slot.
    assert conflict_pairs(i, q.variables) == [(0, 2), (1, 3)]
    feasible = []
    for values in product([0, 1], repeat=4):
        bits = list(values)
        assert q.energy(bits) == pytest.approx(direct_energy(i, q, bits), abs=1e-12)
        decoded = decode(i, q, bits)
        if decoded.validation.feasible:
            feasible.append(decoded.original_objective)
            assert q.energy(bits) == pytest.approx(scale * decoded.original_objective)
            assert encode(i, q, decoded.assignment) == bits
        else:
            assert decoded.validation.violations and decoded.original_objective is None
            assert q.energy(bits) >= scale * q.penalty
    assert sorted(feasible) == [1, 5]
    assert TimetableQubo.model_validate_json(q.model_dump_json()) == q
    verify_artifact(i, q)


def test_weak_penalty_counterexample():
    d = fixture()
    d["courses"] = d["courses"][:1]
    d["preferences"] = [
        {"course_id": "Math", "room_id": "R1", "slot_id": s["id"], "penalty": 10}
        for s in d["slots"]
    ]
    i = TimetableInstance.model_validate(d)
    q = compile_qubo(i, penalty=1)
    assert not q.penalty_sufficient
    assert q.energy([0, 0]) < q.energy([1, 0])
    assert not decode(i, q, [0, 0]).validation.feasible


def test_conflicts_and_unknown_assignments():
    i = instance()
    candidate = TimetableAssignment.model_validate(
        {"assignments": [{"course_id": c.id, "room_id": "R1", "slot_id": "S1"} for c in i.courses]}
    )
    assert {v.code for v in validate_assignment(i, candidate).violations} == {
        "room_conflict",
        "lecturer_conflict",
        "cohort_conflict",
    }
    with pytest.raises(ValueError):
        original_objective(i, candidate)
    candidate.assignments[0].room_id = "unknown"
    assert "unknown_reference" in {v.code for v in validate_assignment(i, candidate).violations}
    candidate.assignments = []
    assert len(validate_assignment(i, candidate).violations) == 2


@pytest.mark.parametrize("seed", range(12))
def test_seeded_small_property_cross_checks(seed):
    rng = random.Random(seed)
    d = fixture()
    d["rooms"].append({"id": "R2", "capacity": rng.choice([10, 30])})
    d["courses"][1]["lecturer_id"] = "L2"
    d["lecturer_ids"].append("L2")
    d["courses"][1]["cohort_ids"] = rng.choice([[], ["G1"]])
    d["preferences"] = [
        {"course_id": c["id"], "room_id": r["id"], "slot_id": s["id"], "penalty": rng.randrange(6)}
        for c in d["courses"]
        for r in d["rooms"]
        for s in d["slots"]
    ]
    i = TimetableInstance.model_validate(d)
    oracle, native = enumerate_solve(i), cp_sat_solve(i, seed=seed)
    assert oracle.objective == native.objective and native.proven_optimal
    q = compile_qubo(i)
    minimum = float("inf")
    for values in product([0, 1], repeat=len(q.variables)):
        bits = list(values)
        energy = q.energy(bits)
        assert energy == direct_energy(i, q, bits)
        minimum = min(minimum, energy)
        dec = decode(i, q, bits)
        assert dec.validation.feasible == (energy < q.penalty)
    assert minimum == oracle.objective


def test_caps_and_tampering():
    d = fixture()
    d["slots"] = [{"id": f"s{k}", "label": str(k), "order": k} for k in range(10)]
    d["preferences"] = []
    i = TimetableInstance.model_validate(d)
    with pytest.raises(ValueError, match="16"):
        compile_qubo(i)
    with pytest.raises(ValueError):
        enumerate_solve(i, limit=1)
    q = compile_qubo(instance())
    modified = copy.deepcopy(q)
    modified.offset += 1
    with pytest.raises(ValueError):
        verify_artifact(instance(), modified)
    for bits in [[True, 0, 0, 0], [0, 0], [-1, 0, 0, 0]]:
        with pytest.raises(ValueError):
            q.energy(bits)
    for timeout in [True, 0, 61, float("nan")]:
        with pytest.raises(ValueError):
            cp_sat_solve(i, timeout_s=timeout)


def test_ties_capacity_and_protocol():
    from quantum_workload_studio.domains.timetable import TimetableProblem

    d = fixture()
    d["preferences"] = []
    i = TimetableInstance.model_validate(d)
    problem = TimetableProblem()
    assert problem.validate_input(d) == i
    assert problem.build_classical_model(i, "cp_sat").instance == i
    with pytest.raises(ValueError):
        problem.build_classical_model(i, "quantum_local")
    assert problem.summarize_instance(i)["courses"] == 2
    q = problem.to_qubo(i)
    costs = []
    for values in product([0, 1], repeat=4):
        dec = problem.decode_assignment(i, q, list(values))
        if dec.validation.feasible:
            costs.append(problem.evaluate_original_objective(i, dec.assignment))
            assert problem.check_hard_constraints(i, dec.assignment).feasible
    assert costs == [0, 0]
    assert cp_sat_solve(i).objective == enumerate_solve(i).objective == 0
    d["rooms"][0]["capacity"] = 1
    i = TimetableInstance.model_validate(d)
    q = compile_qubo(i)
    assert q.variables == [] and q.energy([]) == direct_energy(i, q, []) == 2
    candidate = TimetableAssignment.model_validate(
        {
            "assignments": [
                {"course_id": c.id, "room_id": "R1", "slot_id": s.id}
                for c, s in zip(i.courses, i.slots)
            ]
        }
    )
    assert {v.code for v in validate_assignment(i, candidate).violations} == {"capacity"}


def test_native_unknown_is_not_a_proof():
    answer = cp_sat_solve(instance(), timeout_s=1e-9)
    assert answer.native_status == "UNKNOWN"
    assert answer.assignment is None and answer.objective is None
    assert not answer.proven_optimal and not answer.proven_infeasible
    assert answer.best_objective_bound is not None


@pytest.mark.parametrize("field", ["schema_version", "encoding_version"])
@pytest.mark.parametrize("value", [True, 1.0, "1", 2, None])
def test_qubo_versions_are_strict(field, value):
    data = compile_qubo(instance()).model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        TimetableQubo.model_validate(data)
    data.pop(field)
    with pytest.raises(ValidationError):
        TimetableQubo.model_validate(data)


def test_actual_native_feasible_is_not_optimal(monkeypatch):
    from ortools.sat.python import cp_model

    constructor = cp_model.CpSolver

    def first_solution_solver():
        solver = constructor()
        solver.parameters.cp_model_presolve = False
        solver.parameters.stop_after_first_solution = True
        return solver

    monkeypatch.setattr(cp_model, "CpSolver", first_solution_solver)
    answer = cp_sat_solve(instance())
    assert answer.native_status == "FEASIBLE"
    assert answer.validation.feasible and not answer.proven_optimal
    assert answer.best_objective_bound <= answer.objective
