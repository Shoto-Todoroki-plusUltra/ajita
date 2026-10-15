# Quantum Workload Studio — Codex Implementation Brief

Version: 0.1 | Prepared: 13 October 2026 | Status: implementation specification, not a research novelty claim.

## Mission
Build an open-source, locally usable, hybrid classical/quantum optimization application serving two real use cases: (1) route planning and (2) timetabling/scheduling. Both domains must share a carefully designed problem API, an optional QUBO/Ising compilation pathway, solution decoders and constraint validators, plus classical and quantum execution adapters. We are NOT claiming a quantum speedup.

Long-range vision: a user-facing software layer that chooses an appropriate computing method and can later exploit quantum hardware when genuine benefit is demonstrated. Near-term objective: an honest, reproducible, admissions-quality engineering/research prototype before January 2027.

## Non-negotiable design principles
1. No invented performance measurements, quantum advantage, research novelty, or blanket claim that bigger problems are better on a QPU. A local quantum simulator runs classically.
2. Do not force every domain instance into QUBO. A first-class classical formulation must remain available. Expose unsupported QUBO transformations cleanly.
3. Always verify feasibility and report original-objective quality for decoded solutions. A low QUBO energy is not a valid solution when hard constraints are violated.
4. Use existing prior art and established packages rather than rebuilding Qiskit, OR-Tools, or general-purpose circuit compilers.
5. Classical baselines must be credible: OR-Tools routing/CP-SAT where appropriate; brute-force or dynamic programming as exact oracle on tiny TSP instances; tiny timetable exhaustive enumerator if tractable.
6. Reproducibility: fixed random seeds; environment lockfile; test fixtures; serialized instances/results; record device information, compiler settings, timing definitions, timeouts, shots, and algorithm parameters.
7. No paid/cloud jobs without affirmative user permission, credential configuration, and an explicit review of expected charges. No IBM token in browser, logs, .env committed to git, or telemetry.
8. Maintain a clean distinction between the user's idea/design direction and code generated/implemented by Codex. Document human review and actual testing truthfully.
9. Phase gates: implement one complete tested vertical slice before extending to another domain. Avoid grand agent architecture or speculative optimization policies in the initial MVP.
10. Qiskit / IBM APIs evolve; verify current official docs, pin compatible dependency versions, and don't copy deprecated SamplerV1 examples.

## Intended users and problem scope
### Domain A: Routing
- MVP A1: symmetric Traveling Salesperson Problem (TSP), 4–8 locations for complete QUBO/quantum-path experiments; support somewhat larger classical-only instances. Input is coordinates or a nonnegative symmetric distance matrix, with clear distance units and chosen start/depot.
- Outputs: route, tour distance, feasibility, method used, measured execution time, QUBO encoding metrics when applicable.
- Later A2 (separate phase): capacitated Vehicle Routing Problem (CVRP) with depot, vehicle capacities, demands, realistic classical OR-Tools solver. Do NOT promise a scalable or generally faithful QUBO for CVRP; mark unsupported cases or restrict to separately validated small cases.
- Never pass Euclidean distances off as road travel times; real road routing needs map/traffic data and its own licensed data source.

### Domain B: Timetabling
- MVP B1: small classroom timetable assigning courses to discrete timeslots and rooms, with fixed room capacity, no lecturer conflict, no room collision, simple group/student-cohort conflicts, and optional soft preferences.
- Hard constraints are always enforced or violation-labelled; objective measures soft-constraint penalty after hard feasibility.
- Use OR-Tools CP-SAT baseline; for small bounded B1 examples create optional binary QUBO encoding and a decoder/validator.
- Not a hospital workforce/school district/industrial job-shop solver. Those are later, separate formulations.

## Mathematical representation
Shared typed domain/problem protocol with methods: `validate_input`, `build_classical_model`, `to_qubo` (optional or explicit unsupported), `decode_assignment`, `evaluate_original_objective`, `check_hard_constraints`, `summarize_instance`.

QUBO convention: minimize x^T Q x for x ∈ {0,1}^n. Choose and document either full symmetric Q or upper-triangular coefficient conventions, never silently mix. Store variable names/order, constant offset, scaling, penalty coefficients, conversion provenance, units, and an invertible decoding map where supported. Ensure numerical tests compare the QUBO energy against the direct expanded expression on random binary assignments. Objective interpretation must include constant offset. Add strict JSON schema/version for portable QUBO export and import; call this **our interoperable format**, not an industry standard.

Conversions can use qiskit-optimization `QuadraticProgramToQubo` where valid. Check the resulting converter's assumptions; penalty strength matters. For tiny instances enumerate assignments to demonstrate hard constraints cannot be overridden by attractive infeasible energies under chosen penalty. Document when penalties cannot be proven adequate.

TSP canonical binary formulation: x[i,t] indicates city i occupies position t. Exactly one city per position; each city appears exactly once; tour cost sum_t sum_ij d_ij x[i,t] x[j,(t+1) mod n]. Fix a depot/first city to reduce symmetry when appropriate, and document resulting qubit count. Test against exhaustive route enumeration for tiny graphs.

Timetable B1 binary formulation: x[c,r,t] indicates course c is assigned room r at time t; use one-hot assignment constraints, room and lecturer/cohort conflicts, capacity admissibility, plus soft preference penalties. Clearly cap variable count and reject quantum mode when exceeding configured limits.

## Execution adapters
1. Classical: exact tiny-instance reference solver, OR-Tools TSP routing and CP-SAT timetable, plus optional simple heuristic. Stable return schema.
2. Quantum local: Qiskit-compatible QUBO -> Ising conversion and a small QAOA experiment using current maintained APIs; local sampler/estimator with small shot counts, controlled seeds, recorded circuit depth/gate count and transpilation settings. For oversized instances fail with a useful resource explanation rather than hang/crash.
3. IBM cloud QPU: OPTIONAL, disabled by default; design an adapter interface and dry-run transpilation/resource report first. Implement real paid execution only as a later, opt-in phase; make an explicit human approval gate and never estimate billable charge as guaranteed. Use latest documented IBM Quantum Compute primitives at integration time.
4. Backend decision logic in v1 is conservative rules: prefer strong classical baseline for ordinary user jobs; simulator for opt-in research comparison; QPU only opt-in. Do not train a 'quantum advantage predictor' without actual data.

## Proposed stack (adjust only with explained justification)
- Python 3.11/3.12 compatible, FastAPI + Pydantic for backend and typed JSON API.
- Qiskit core, qiskit-optimization where supported, Qiskit Aer for local simulation if supported on developer's macOS architecture.
- Google OR-Tools for classical routing and scheduling.
- React + TypeScript + Vite for clean user interface (not a huge component library); simple map-like coordinate visualization and timetable grid; no commercial map SDK for MVP.
- pytest + hypothesis when justified; Vitest and Playwright for front-end tests if feasible.
- uv or pip-tools plus pinned lockfile; pre-commit lint/format checks; GitHub Actions CI on Linux and macOS if practical.
- Standard Mac development instructions, including macOS arm64 and x86 where possible; no mandatory Docker or paid cloud account.

## API shape (proposed, subject to implementation review)
- `POST /api/problems/tsp/solve` — typed instance + method (classical|quantum_local); result.
- `POST /api/problems/timetable/solve` — typed instance + method; result.
- `POST /api/qubo/compile` — supported problem -> QUBO with encoding metadata or explicit unsupported error.
- `POST /api/experiments/compare` — controlled comparative run returning methods, validation, timing and metadata.
- `GET /api/health`.
- QPU endpoint, if any, must require opt-in and server-side auth, and be OFF by default.

## UI
- Home: choose Routing or Timetable.
- Routing: example preset, coordinate input or matrix import, route diagram, metric table, solver method chooser.
- Timetable: courses/rooms/slots/lecturers inputs, visual calendar, conflict/penalty explanation.
- Advanced inspection: QUBO variable count, penalty terms, circuit estimates, job cost warning, method comparison.
- Distinguish actually measured runs from estimated quantities. Show 'not available' rather than fake numbers.

## Testing and evaluation acceptance criteria
- Property-based and fixed-fixture tests for input validation, QUBO energy evaluation, conversion/decoding, hard constraints and objective round trips.
- On tiny TSP (e.g., 4–6 cities), exhaustive enumeration produces a verified optimum. Compare every method to it when feasible.
- On tiny timetables, prove the expected feasibility/infeasibility and compare CP-SAT optimum with an enumerator where practical.
- Tests for cases where QUBO penalty is deliberately too weak and should flag feasibility failure.
- Real classical benchmarks on fixed data, multiple seeds, warmup protocol and separate timing for formulation/compile/solver/network/queue. Quantum quality should be compared at matched user-relevant objectives and sampling budgets.
- Report median, dispersion, success/feasibility rate, optimality gap where known, peak memory if measured, simulator qubit count and circuit depth, and monetary estimates ONLY where grounded. Never count hardware/network queue time as simulator speedup.
- Unit tests, integration tests, documented manual UI test, regression fixtures, reproducible benchmark CLI and raw CSV/JSON artifacts.
- README with unambiguous 'no practical quantum speedup demonstrated' disclaimer unless compelling evidence is actually measured.

## Work phases: pause for review at each gate
### Phase 0: discovery, plan, prior-art review (first Codex task)
Inspect repository (if any), current official package docs, Mac compatibility, research prior art (OR-Tools/Qiskit/MQT/optimization products). Produce `docs/PRIOR_ART.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PHASE_PLAN.md`, and explicit questions/risks. DO NOT implement until user reviews the plan.
### Phase 1: minimal vertical slice
Project scaffold; one tiny TSP example; classical exact oracle + OR-Tools; validated QUBO builder/round-trip; local quantum tiny example; tests; basic API + simple end-to-end UI.
### Phase 2: timetable
Timetabling CP-SAT and small QUBO; correctness tests; UI grid; shared interface refactor only where proven useful.
### Phase 3: experiments
Backend comparisons with reproducible instances, quality/feasibility checks, circuit properties, timing and resource reporting; compare against relevant prior art.
### Phase 4: QPU research adapter and release
Dry-run transpilation against IBM device properties; optional user-authorized hardware run; docs, tests, reproducibility artifacts and research-style report. Only progress here after actual evidence and user review.
### Separate future phase
CVRP, production road maps, learned backend selection, multiple QPUs; not part of the MVP.

## Deliverables expected from Codex
Codebase with README, environment lockfile, example data, CLI, API, UI, tests, CI config, docs architecture, literature/prior-art inventory with source URLs, benchmark methodology, benchmark results generated from actual executed code, and honest caveats. Write a concise `docs/IMPLEMENTATION_REPORT.md` stating exactly what was implemented, what was run, passing/failing tests, commands/output, and unimplemented items.

## Official starting references (revalidate against newest docs before coding)
- https://developers.google.com/optimization
- https://developers.google.com/optimization/cp
- https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html
- https://quantum.cloud.ibm.com/docs/en/guides/qiskit-runtime-primitives
- https://quantum.cloud.ibm.com/docs/api/qiskit-ibm-runtime/sampler-v2
- https://chatgpt.com/features/codex-get-started/

## Research framing
Project novelty is UNVERIFIED. Contribution should arise from controlled experiments, perhaps formulation/penalty robustness, feasibility-aware translation and comparison, or an experimentally validated policy for choosing a backend. Do not describe generic QUBO use, QAOA, Qiskit interfacing, backend selection, or classical/quantum comparison as novel by themselves. Future academic writeup must cite prior art accurately and separate hypothesis from validated results.
