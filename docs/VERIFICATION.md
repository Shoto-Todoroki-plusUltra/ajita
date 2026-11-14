# Tests and limitations

Ajita checks solutions in the original problem domain. A solver finishing successfully or a bitstring having low QUBO energy is not enough to establish feasibility.

## Mathematical checks

- The four-city TSP example has six depot-fixed tours. The exact optimum is 4. All **512** reduced binary assignments are checked against the direct objective, expanded QUBO and Ising energies; six are feasible and 506 are invalid.
- Tiny classroom fixtures are checked with both an independent original-domain enumerator and CP-SAT. Tests include feasible, infeasible, tied and capacity-impossible cases.
- TSP/B1 mapping certificates cover **3,897** fixture/penalty rows, including one constant-only case. These are mathematical checks, not quantum sampling experiments.
- Tests cover coefficient signs, offsets, scaling, penalties, non-palindromic bitstrings and measurement/layout conventions.

[Four-city assignments](../evidence/admissions-preview/public/four-city-512.json) · [TSP operator certificate](../evidence/admissions-preview/public/tsp-operator-512.json) · [Timetable certificates](../evidence/admissions-preview/public/b1-mathematical-summary.json) · [Mapping certificate](../evidence/admissions-preview/public/mapping-3897.json)

## Executed software checks

The packaged source was tested on native macOS arm64 using Python 3.12.13 and the pinned dependencies:

| Check | Recorded result |
|---|---|
| Classical/API selection | 650 passed; one sampler-dependent case deferred |
| Additional packaging cases | Four new cases passed; seven including existing archive tests |
| Extracted source archive | 654 passed; one sampler-dependent case deferred |
| Frontend components | 12 passed |
| Real classical browser flows | Seven passed |
| Build, schema/type checks and normal pre-commit hook | Passed |

The later protected research test selection recorded **5,152 passing parametrized cases with six sampler-dependent tests deselected**. It is not 5,152 distinct practical problems or an end-to-end timetable quantum run. Those six tests cover real quantum API execution, QAOA reproducibility, quantum timeout/CLI behavior, and statevector/Aer measurement-layout sampling.

[Classical test log](../evidence/admissions-preview/public/classical.log) · [Browser tests](../evidence/admissions-preview/public/browser-final.log) · [Component tests](../evidence/admissions-preview/public/vitest.log) · [Build](../evidence/admissions-preview/public/build.log) · [Protected-test policy](../evidence/admissions-preview/public/historical-3bs-policy.json)

## Local quantum evidence

An earlier four-city TSP StatevectorSampler run used 16 evaluations of 256 shots: **61 feasible and 4,035 invalid samples**, with best feasible original cost 4. The optimizer's success flag was false because its evaluation budget was exhausted. The best route is selected across the full trace, not claimed to represent the final-parameter distribution. A separate no-feasible run retains a null candidate and gap.

These are recorded CPU simulations, not fresh measurements or evidence of quantum advantage. B1 has verified mapping mathematics but no endorsed quantum execution path.

[Recorded TSP trace](../evidence/admissions-preview/public/historical-tsp-statevector.json) · [No-feasible result](../evidence/admissions-preview/public/historical-tsp-no-feasible.json)

## Known limits

- Historical 20–30-second OR-Tools startup/tail-latency failures remain unexplained. Passing later runs does not establish a fix.
- RSS and deadline checks are software guards, subject to scheduling and polling delays. Cleanup after abrupt parent/OS termination is not guaranteed.
- A fresh locked frontend install and build passed. The latest Python checks reused an existing pinned environment rather than reinstalling it.
- Linux, Windows, Intel Mac, other browsers and remote CI have not been verified here. A CI workflow is provided without claiming a remote pass.
- The unfinished internal B1 sampling runner has an evidence-retention failure path and is not part of the supported application.

Portable evidence files retain original source hashes in [the evidence index](../evidence/admissions-preview/public/EVIDENCE_INDEX.json). Some logs have machine paths and synthetic security-test identifiers removed; they are labeled projections rather than unchanged raw records. Test counts describe software cases, not statistical research trials.
