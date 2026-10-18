"""B1 implements the brief's problem interface without a universal model IR."""

from dataclasses import dataclass
from typing import Literal

from quantum_workload_studio.models.timetable import (
    TimetableInstance,
    original_objective,
    validate_assignment,
)
from quantum_workload_studio.qubo.timetable import compile_qubo, decode, verify_artifact


@dataclass(frozen=True)
class ClassicalModelHandle:
    instance: TimetableInstance
    solver_id: Literal["cp_sat", "enumeration"]


class TimetableProblem:
    def validate_input(self, data):
        return TimetableInstance.model_validate(data)

    def build_classical_model(self, instance, solver_id):
        if solver_id not in ("cp_sat", "enumeration"):
            raise ValueError("unsupported timetable solver")
        return ClassicalModelHandle(instance, solver_id)

    def to_qubo(self, instance, **options):
        return compile_qubo(instance, **options)

    def decode_assignment(self, instance, artifact, bits):
        verify_artifact(instance, artifact)
        return decode(instance, artifact, bits)

    def evaluate_original_objective(self, instance, assignment):
        return original_objective(instance, assignment)

    def check_hard_constraints(self, instance, assignment):
        return validate_assignment(instance, assignment)

    def summarize_instance(self, instance):
        return {
            "kind": "timetable",
            "courses": len(instance.courses),
            "rooms": len(instance.rooms),
            "slots": len(instance.slots),
            "instance_hash": instance.instance_hash(),
        }
