"""Small typed domain protocol; no speculative multi-domain framework."""

from dataclasses import dataclass
from typing import Literal, Protocol

from quantum_workload_studio.models.tsp import (
    TspAssignment, TspInstance, ValidationReport, check_hard_constraints, evaluate_original_objective,
)
from quantum_workload_studio.qubo.tsp import QuboArtifact, DecodeOutcome, compile_qubo, decode_assignment


@dataclass(frozen=True)
class ClassicalModelHandle:
    instance: TspInstance
    solver_id: Literal["exact_tsp", "ortools_tsp"]


class Problem(Protocol):
    def validate_input(self, data: dict) -> TspInstance: ...
    def build_classical_model(self, instance: TspInstance, solver_id: str) -> ClassicalModelHandle: ...
    def to_qubo(self, instance: TspInstance) -> QuboArtifact: ...
    def decode_assignment(self, instance: TspInstance, bits: list[int]) -> DecodeOutcome: ...
    def evaluate_original_objective(self, instance: TspInstance, assignment: TspAssignment) -> float: ...
    def check_hard_constraints(self, instance: TspInstance, assignment: TspAssignment) -> ValidationReport: ...
    def summarize_instance(self, instance: TspInstance) -> dict: ...


class TspProblem:
    def validate_input(self, data: dict) -> TspInstance:
        return TspInstance.model_validate(data)

    def build_classical_model(self, instance: TspInstance, solver_id: str) -> ClassicalModelHandle:
        if solver_id not in ("exact_tsp", "ortools_tsp"):
            raise ValueError("unsupported classical solver")
        return ClassicalModelHandle(instance, solver_id)

    def to_qubo(self, instance: TspInstance) -> QuboArtifact:
        return compile_qubo(instance)

    def decode_assignment(self, instance: TspInstance, bits: list[int]) -> DecodeOutcome:
        return decode_assignment(instance, bits)

    def evaluate_original_objective(self, instance: TspInstance, assignment: TspAssignment) -> float:
        return evaluate_original_objective(instance, assignment)

    def check_hard_constraints(self, instance: TspInstance, assignment: TspAssignment) -> ValidationReport:
        return check_hard_constraints(instance, assignment)

    def summarize_instance(self, instance: TspInstance) -> dict:
        return {"kind": "tsp", "city_count": len(instance.city_ids), "depot_id": instance.depot_id,
                "distance_unit": instance.distance_unit, "instance_hash": instance.instance_hash()}
