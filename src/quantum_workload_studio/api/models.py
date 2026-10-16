"""HTTP contracts used to generate the frontend's OpenAPI TypeScript models."""

from typing import Annotated, Literal

from pydantic import Field

from quantum_workload_studio.execution.local import LocalOptions
from quantum_workload_studio.models.tsp import (
    StrictModel,
    TspAssignment,
    TspInstance,
    ValidationReport,
)
from quantum_workload_studio.qubo.tsp import QuboArtifact


class SolveRequest(StrictModel):
    instance: TspInstance
    method: Literal["classical", "quantum_local"] = "classical"
    solver: Literal["exact_tsp", "ortools_tsp"] = "ortools_tsp"
    timeout_s: Annotated[float, Field(gt=0, le=60, allow_inf_nan=False)] = 10.0
    memory_limit_mb: Annotated[int, Field(ge=64, le=1024)] = 512
    scale: Annotated[int, Field(ge=1, le=10**9)] = 1000
    quantum: LocalOptions = Field(default_factory=LocalOptions)

    # The HTTP timeout/memory fields govern the whole request; nested LocalOptions
    # values are echoed after being replaced by those server-bounded limits.


class QuantumSummary(StrictModel):
    raw_shots: int
    evaluations: int
    feasible_shots: int
    invalid_shots: int
    feasible_fraction: float | None
    invalid_fraction: float | None
    candidate_outcome: str
    optimizer_success: bool | None
    optimizer_message: str | None
    exact_reference: float
    absolute_gap: float | None
    raw_counts: dict[str, int]
    selection_policy: str


class ApiResult(StrictModel):
    schema_version: Literal[1] = 1
    instance_hash: str
    method: Literal["classical", "quantum_local"]
    solver_id: str
    execution_status: str
    outcome: str
    assignment: TspAssignment | None
    validation: ValidationReport
    objective: float | None
    objective_unit: str
    proven_optimal: bool
    total_elapsed_s: float
    quantum: QuantumSummary | None = None
    worker: dict
    effective_options: dict


class CompileRequest(StrictModel):
    instance: TspInstance


class InspectRequest(StrictModel):
    instance: TspInstance
    qubo: QuboArtifact
    bits: Annotated[str, Field(min_length=1, max_length=49, pattern="^[01]+$")]


class InspectResult(StrictModel):
    energy: float
    assignment: TspAssignment | None
    validation: ValidationReport
    original_objective: float | None


class ApiError(StrictModel):
    code: str
    message: str
    details: list[dict] = Field(default_factory=list)


class ErrorResponse(StrictModel):
    error: ApiError
