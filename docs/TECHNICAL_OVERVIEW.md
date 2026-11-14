# Ajita: verified translation across two small optimization domains

Ajita is a local research/teaching prototype, not a novel quantum algorithm or an industrial optimizer. Its software-engineering contribution is an inspectable chain from strict original input through established solvers or optional binary encodings to independent feasibility checking and honest result reporting. 

## Original problems and credible classical references

**Symmetric travelling salesperson.** Given ordered cities, a depot and finite nonnegative symmetric costs, choose one closed tour visiting every city once and minimize its original total cost. Input is either a supplied matrix or planar Euclidean coordinates; neither represents road travel times. The tiny exact solver enumerates depot-fixed permutations. OR-Tools routing uses integer costs with an explicit scale/rounding policy, then the original float objective is recomputed. Its heuristic result is not an optimum proof. On the supplied four-city fixture, all six permutations cost 4 or 6; the cost-4 witnesses attain the independent lower bound of four edges costing at least one.

**B1 classroom assignment.** Each course has one single-slot event, enrollment, lecturer and declared cohorts. Choose a capacity-admissible room and a discrete nonoverlapping slot. Enforce exactly one placement per course; prohibit room, lecturer and intersecting-cohort collisions. Minimize additive nonnegative integer preference penalties, with missing triples costing zero. Native OR-Tools CP-SAT groups resource constraints independently of QUBO generation; its native status and meaningful bound remain visible. FEASIBLE is not OPTIMAL, UNKNOWN is not INFEASIBLE. A tiny exhaustive oracle enumerates original room/slot assignments, including capacity-invalid choices, as a separate reference. The two-course preset has two feasible assignments of costs 1 and 5.

Strict Pydantic models reject malformed references, duplicate IDs/preferences, extra fields, nonfinite values and inappropriate type coercions. Original validators operate on candidate tours/placements independently of solver success and binary energy. Invalid candidates retain violations and have no valid original objective. No repair, hidden fallback or sorting of selected bits supplies a solution.

## Optional QUBO encodings

The portable convention is upper triangular:

```text
E(x) = offset + Σ_i Qii xi + Σ_(i<j) Qij xi xj,  xi ∈ {0,1}.
```

Off-diagonal terms are counted once; x²=x. Whole-energy scale multiplies coefficients **and** the offset. Artifacts retain ordered variables, domain references, version/encoder, source-instance hash, penalties and conversion provenance. Canonical recompilation checks imports; a converter result is not automatically trusted. This is the project's versioned format, not an industry standard or general optimization IR.

For TSP, x[i,t] selects a city at a tour position. Fixing the depot reduces the active width to (n−1)²: nine bits for four cities. Cost includes depot edges and consecutive positions. Squared row/column one-hot residuals enforce permutations. With U=n·d_max and nonnegative costs, choosing A>U is a conservative sufficient separation bound. For the preset A=16, QUBO offset=96; exhaustive enumeration finds six feasible and 506 invalid bitstrings. Weak penalties can make invalid low-energy states attractive; the original validator still rejects them.

For B1, variables exist only for capacity-admissible (course,room,slot) triples. The expression is preference cost plus A times squared exact-one residuals plus A for each deduplicated cross-course conflict pair. A pair sharing room, lecturer and cohort is penalized once. With U equal to the sum of maximum admissible per-course preference, A=U+1 separates invalid energy from feasible cost **if a feasible assignment exists**. It does not create feasibility. An empty group retains its positive constant penalty. Infeasible zero-variable controls remain invalid, not zero-qubit QAOA successes.

## Ising and sampling boundaries

Substitute **xi=(1−Zi)/2**. The separate identity coefficient is

```text
k = offset + Σ_i Qii/2 + Σ_(i<j) Qij/4,
hi = −Qii/2 − Σ_(j≠i) Q[min(i,j),max(i,j)]/4,
Jij = Qij/4.
```

The diagonal `SparsePauliOp` stores h and J; k is omitted from phase evolution only as a global phase, then included in energy comparisons. Tests compare a separately computed direct expression, QUBO, classical Ising and SDK basis expectations. Qiskit qubit i occupies Pauli character q−1−i; displayed register x0 is rightmost. B1 inspection strings instead use left-to-right **index order**. Non-palindromic fixtures and nonidentity layouts prevent an accidental reversal from looking correct.

The mapping certificate checks 3,897 fixture/policy rows: 3,896 SDK-capable basis states plus one classical constant-only control. It does not execute B1 QAOA. B1's public solve endpoint and UI remain classical-only. Internal research mapping/normalization preflight is not a public quantum solver. An unfinished internal B1 sampling draft is not part of the supported application.

The TSP path uses Qiskit core V2 local primitives, a shallow QAOA ansatz and bounded SciPy COBYLA. All received counts enter the penalized loss and the feasible/invalid denominator. Best feasible **original** objective is selected across the entire optimizer trace, separately from optimizer convergence and execution status. No feasible shots means null best/gap. A historical 4,096-shot run produced 61 feasible shots and cost 4 while optimizer success was false/MAXFUN. Finding a good sample does not establish convergence, a new algorithm or speedup; statevector simulation runs classically.

## Application boundary and resource limits

The React/Vite client calls a loopback FastAPI service; API and CLI reuse domain/service logic. Quantum SDKs load lazily. Spawned worker supervision handles deadlines, cancellation, sampled RSS and termination/kill cleanup; one active job per server process, no queue. A completed event followed by forced termination is an unclean exit. No kernel hard memory guarantee, hard real-time deadline or abrupt-parent-death cleanup guarantee is made. Backend computation time excludes HTTP/browser latency; nested timings must not be added as disjoint intervals.

| Protective ceiling | Current implementation |
|---|---|
| TSP input / exact / QUBO | 4–200 cities / at most 8 / 4–8 |
| Local TSP simulation | at most 16 active variables; p≤2, ≤50 evaluations, ≤4,096 shots/evaluation, ≤60 s; API additionally caps 8,192 requested trace shots |
| B1 domain | 50 courses, 20 rooms, 40 slots; ≤20,000 assignment cells/preferences |
| B1 exhaustive / QUBO | ≤65,536 original combinations / ≤16 admissible variables |
| API | ≤2 MiB JSON, one process/worker, ≤60 s; default 512 MiB sampled worker-RSS request |

These are refusals/guardrails, not scalability promises. The initial target is native macOS arm64/Python 3.12 with separate classical and optional-quantum locks. The historical intermittent 20–30-second OR-Tools startup/tail-latency cause remains unresolved. Other platforms, remote CI, public hosting and QPU hardware are unverified. There is no recurrence, individual sectioning, fleet capacity, CVRP, road data, account system or universal scheduling claim.

## Evidence and admissible conclusions

[VERIFICATION](VERIFICATION.md) links actual records, mathematical certificates and privacy-safe historical projections. The 5,152-case protected test run contains selected/parametrized software cases and defers six sampler-dependent tests. It is not a B1 quantum run. Recorded quantum outputs retain their execution dates and limitations. Negative findings—invalid samples, weak-penalty ties, MAXFUN and missing feasible outcomes—are part of the evidence, not excluded successes.
