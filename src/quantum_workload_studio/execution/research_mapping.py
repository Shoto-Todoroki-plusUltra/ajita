"""Internal, canonical TSP/B1 mapping boundaries. No B1 sampler/optimizer entry point.

Hash equality is integrity/provenance checking, not a cryptographic signature or
owner approval. Original encoders and validators remain authoritative.
"""

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field, model_validator

from quantum_workload_studio.models.timetable import TimetableInstance
from quantum_workload_studio.models.tsp import StrictModel, TspInstance
from quantum_workload_studio.qubo.basis import IsingPolynomial, to_ising_basis
from quantum_workload_studio.qubo.timetable import TimetableQubo, decode
from quantum_workload_studio.qubo.timetable import verify_artifact as verify_b1
from quantum_workload_studio.qubo.tsp import QuboArtifact, bits_from_display
from quantum_workload_studio.qubo.tsp import verify_artifact as verify_tsp

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Normalization = Literal["none", "ising_l1"]


def artifact_digest(artifact: QuboArtifact | TimetableQubo) -> str:
    text = json.dumps(artifact.model_dump(), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


class _Request(StrictModel):
    schema_version: Literal[1]
    artifact_sha256: Digest
    normalization: Normalization

    @model_validator(mode="before")
    @classmethod
    def version(cls, data):
        if isinstance(data, dict) and type(data.get("schema_version")) is not int:
            raise ValueError("research interface version must be explicit integer 1")
        return data


class TspResearchInput(_Request):
    artifact: QuboArtifact


class B1ResearchInput(_Request):
    artifact: TimetableQubo


@dataclass(frozen=True)
class Mapping:
    """Immutable coefficient metadata only; no general problem/solver IR."""

    basis: IsingPolynomial
    divisor: float
    normalization: Normalization
    instance_sha256: str
    artifact_sha256: str

    def sparse_operator(self):
        # SDK loads only on explicit mapping use, never classical/API import.
        from qiskit.quantum_info import SparsePauliOp

        n = len(self.basis.linear)
        if n == 0:
            raise ValueError("zero-variable mapping is constant-only; SDK/sampling unsupported")
        terms = []
        for i, h in enumerate(self.basis.linear):
            if h:
                label = ["I"] * n
                label[n - 1 - i] = "Z"
                terms.append(("".join(label), h / self.divisor))
        for i, j, coefficient in self.basis.quadratic:
            if coefficient:
                label = ["I"] * n
                label[n - 1 - i] = label[n - 1 - j] = "Z"
                terms.append(("".join(label), coefficient / self.divisor))
        operator = SparsePauliOp.from_list(terms or [("I" * n, 0.0)]).simplify(atol=0, rtol=0)
        return operator, self.basis.offset / self.divisor

    def metadata(self):
        return {
            "instance_sha256": self.instance_sha256,
            "artifact_sha256": self.artifact_sha256,
            "normalization": self.normalization,
            "normalization_divisor": self.divisor,
            "ising_identity_offset": self.basis.offset,
            "normalized_identity_offset": self.basis.offset / self.divisor,
            "operator_order": "variable i -> qubit i -> Pauli character n-1-i",
        }


def _mapping(instance_hash, artifact, request):
    if artifact_digest(artifact) != request.artifact_sha256:
        raise ValueError("artifact digest mismatch/stale research request")
    if artifact.source_instance_hash != instance_hash:
        raise ValueError("artifact original-instance hash mismatch")
    if len(artifact.variables) > 9:
        raise ValueError("3B-M research mapping supports at most 9 active variables")
    basis = to_ising_basis(artifact)
    values = [basis.offset, *basis.linear, *(c for _, _, c in basis.quadratic)]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Ising expansion overflow")
    l1 = math.fsum([*(abs(h) for h in basis.linear), *(abs(c) for _, _, c in basis.quadratic)])
    if request.normalization == "ising_l1" and (not math.isfinite(l1) or l1 <= 0):
        raise ValueError("ising_l1 requires a nonzero finite nonidentity operator")
    return Mapping(
        basis,
        l1 if request.normalization == "ising_l1" else 1.0,
        request.normalization,
        instance_hash,
        request.artifact_sha256,
    )


def prepare_tsp(instance: TspInstance, request: TspResearchInput):
    # Revalidate copies: mutable nested lists/model_construct/model_copy cannot bypass checks.
    instance = TspInstance.model_validate(instance.model_dump())
    request = TspResearchInput.model_validate(request.model_dump())
    artifact = QuboArtifact.model_validate(request.artifact.model_dump())
    verify_tsp(instance, artifact)
    return artifact, _mapping(instance.instance_hash(), artifact, request)


def prepare_b1(instance: TimetableInstance, request: B1ResearchInput):
    instance = TimetableInstance.model_validate(instance.model_dump())
    request = B1ResearchInput.model_validate(request.model_dump())
    artifact = TimetableQubo.model_validate(request.artifact.model_dump())
    verify_b1(instance, artifact)
    return artifact, _mapping(instance.instance_hash(), artifact, request)


def check_research_options(options):
    from quantum_workload_studio.execution.local import LocalOptions

    options = LocalOptions.model_validate(options.model_dump())
    if (
        options.backend != "statevector"
        or options.reps != 1
        or options.shots > 256
        or options.max_evaluations > 16
        or options.timeout_s > 20
        or options.memory_limit_mb > 512
    ):
        raise ValueError("3B-M research caps: statevector, p=1, 256 shots, 16 calls, 20s, 512 MiB")
    return options


def prepare_b1_sampling_boundary(instance, request, options):
    """Preflight only. No worker spawn, circuit/optimizer or sampler execution."""
    from quantum_workload_studio.execution.local import memory_preflight

    options = check_research_options(options)
    artifact, mapping = prepare_b1(instance, request)
    preflight = memory_preflight(len(artifact.variables), options)
    return {
        "mapping": mapping.metadata(),
        "preflight": preflight,
        "options": options.model_dump(),
        "execution_authorized": False,
        "status": "mapping_only; sampler execution requires separate owner approval",
    }


def decode_b1_readouts(instance, request, raw_counts, logical_to_classical):
    """Validation boundary for supplied readouts, not evidence of sampler execution.

    Requires a single complete named register; classical wiring already embodies
    transpilation layout. Do not apply the physical layout a second time.
    """
    instance = TimetableInstance.model_validate(instance.model_dump())
    artifact, _ = prepare_b1(instance, request)
    n = len(artifact.variables)
    if (
        type(logical_to_classical) is not list
        or len(logical_to_classical) != n
        or any(type(i) is not int for i in logical_to_classical)
        or sorted(logical_to_classical) != list(range(n))
    ):
        raise ValueError("logical-to-classical map must be a complete integer permutation")
    if type(raw_counts) is not dict or len(raw_counts) > 4096:
        raise ValueError("bounded register count dictionary required")
    rows, total, feasible, best = [], 0, 0, None
    for displayed, count in sorted(raw_counts.items()):
        if type(count) is not int or count <= 0:
            raise ValueError("readout counts must be positive integers")
        total += count
        if total > 4096:
            raise ValueError("supplied readout budget exceeds 4096")
        try:
            classical = bits_from_display(displayed, n)
            bits = [classical[c] for c in logical_to_classical]
            outcome = decode(instance, artifact, bits)
            row = {
                "raw_display": displayed,
                "count": count,
                "bits_index_order": bits,
                **outcome.model_dump(),
            }
        except ValueError as exc:
            row = {
                "raw_display": displayed,
                "count": count,
                "bits_index_order": None,
                "assignment": None,
                "original_objective": None,
                "validation": {
                    "checked": True,
                    "feasible": False,
                    "violations": [
                        {"code": "malformed_sample", "entity_ids": [], "message": str(exc)}
                    ],
                },
            }
        rows.append(row)
        if row["validation"]["feasible"]:
            feasible += count
            if best is None or row["original_objective"] < best["original_objective"]:
                best = row
    return {
        "source": "supplied readout validation only; no sampler execution implied",
        "raw_shots": total,
        "feasible_shots": feasible,
        "invalid_shots": total - feasible,
        "feasible_fraction": feasible / total if total else None,
        "invalid_fraction": (total - feasible) / total if total else None,
        "best_feasible": best,
        "decoded_rows": rows,
    }


def resolve_tsp_worker_input(instance, options, payload):
    """Recheck serialized research input in the worker before circuit construction."""
    check_research_options(options)
    artifact, mapping = prepare_tsp(instance, TspResearchInput.model_validate(payload))
    operator, offset = mapping.sparse_operator()
    return artifact, operator, offset, mapping.divisor, mapping.metadata()
