"""Classical Ising basis algebra only: no circuit, sampler or SDK integration."""

import math
from dataclasses import dataclass

from quantum_workload_studio.qubo.tsp import QuboArtifact, validate_bits


@dataclass(frozen=True)
class IsingPolynomial:
    offset: float
    linear: tuple[float, ...]
    quadratic: tuple[tuple[int, int, float], ...]

    def energy(self, bits: list[int]) -> float:
        validate_bits(bits, len(self.linear))
        z = [1-2*x for x in bits]
        return math.fsum([self.offset, *(a*z[i] for i, a in enumerate(self.linear)),
                          *(a*z[i]*z[j] for i, j, a in self.quadratic)])


def to_ising_basis(qubo: QuboArtifact) -> IsingPolynomial:
    linear = [0.0] * len(qubo.variables)
    constant = [qubo.offset]
    pairs = []
    for term in qubo.terms:
        i, j, a = term.i, term.j, term.coefficient
        if i == j:
            constant.append(a/2)
            linear[i] -= a/2
        else:
            constant.append(a/4)
            linear[i] -= a/4
            linear[j] -= a/4
            pairs.append((i, j, a/4))
    return IsingPolynomial(math.fsum(constant), tuple(linear), tuple(pairs))
