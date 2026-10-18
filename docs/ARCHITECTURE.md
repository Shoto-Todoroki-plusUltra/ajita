# Architecture proposal

Current status (18 October 2026): the owner accepted the targeted 1C remediation and separately authorized **Phase 2 B1 only**. Implementation awaits independent Phase 2 acceptance. Historical status notes below describe their original checkpoints; they do not authorize Phase 3–4. The original TSP/QAOA paths and artifacts remain preserved. The historical OR-Tools cold-start/tail-latency risk is unresolved.

Historical implementation status (16 October 2026): the user subsequently approved 1A, 1B and **1C only**, separately. The proposal below remains the design record; actual contracts, measurements and limits are in `schemas/openapi.json` and [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md). No Phase 2–4 work is authorized.

Phase 0 only, revised 14 October 2026 after critical review. Architecture is provisionally accepted; Phase 1 is not authorized. All paths, schemas and limits below are proposed contracts, not implemented features. [PROJECT_BRIEF.md](../PROJECT_BRIEF.md) remains binding. Source context is in [PRIOR_ART.md](PRIOR_ART.md); trade-offs in [DECISIONS.md](DECISIONS.md).

## Local structure and ownership

One Python package, one React client and one bounded local worker; no agent framework or distributed scheduler. API/CLI call the same solve service. Classical solving never requires Qiskit imports. Optional quantum dependencies load only when requested. CPU work runs in a killable worker process so a request deadline can bound work; cancellation must clean up child processes. Bind development server to loopback, cap request sizes and worker concurrency, and use explicit CORS origins.

```text
docs/                         # these Phase 0 documents; later reports/methodology
pyproject.toml                # Python package + optional quantum/dev dependencies
requirements/                 # pip-tools inputs and platform-specific hash locks
src/quantum_workload_studio/
  models/                     # strict Pydantic input/result/export contracts
  domains/
    protocol.py               # typed Problem[I, A] protocol
    tsp.py                    # validation, objective, constraints, model recipes
    timetable.py              # Phase 2 only
  classical/                  # exact_tsp, ortools_tsp; Phase 2 cp_sat/enumerator
  qubo/                       # coefficients, schema, energy, decoder registry
    tsp.py                    # explicit reduced TSP encoder
    mapper_adapter.py         # optional successor mapping, after checkpoint 1A
    ising.py                  # tested x=(1-Z)/2 translation
  execution/                  # local V2 sampler/QAOA; resource guard
    ibm.py                    # Phase 4 only, disabled until authorized
  services/                   # solve, process limits, verification, comparisons
  api/                        # FastAPI endpoints/error mapping
  cli.py                      # solve/export; benchmark CLI grows in Phase 3
frontend/
  src/api/                    # types generated from backend schema, client
  src/features/routing/       # coordinate sketch/matrix input/result
  src/features/timetable/     # Phase 2 only
  src/components/             # metrics, violations, resource explanations
  tests/                      # Vitest, Playwright flows
schemas/                      # generated versioned JSON schemas
examples/tsp/                 # serialized deterministic fixtures
tests/{unit,integration,fixtures}/
experiments/                   # Phase 3 configuration, raw artifacts, reports
.github/workflows/            # Phase 1 Linux/macOS CI; no cloud credentials
README.md                     # setup, limits, attribution, honesty disclaimer
```

Do not create future-phase placeholders merely to match this tree. `timetable.py` and `ibm.py` appear only when their phases are approved. Python package/license metadata and Git initialization belong to Phase 1; license choice requires the owner's decision before release.

Checkpoint **1A** creates only the minimal Python mathematical core, fixture, reference solver, decoder, portable schema, tests and a reproducible CLI/report. API, worker process, frontend, optional mapping adapters and QAOA arrive afterward. The directory tree is the full Phase 1 destination, not a scaffold that must all exist before mathematical verification. Checkpoint **1B** tests bounded local execution; **1C** completes the minimal API/UI slice. A passing 1A does not mean QAOA works or that Phase 1 is complete.

## Product boundary and future routing transition

Phase 1 is a symmetric TSP teaching/research solver, **not a real-world delivery-routing service**. It optimizes one closed tour on supplied costs. It has no road network, geocoding, one-way restrictions, traffic, fleet, demand, service-time, time-window or dispatch model. A coordinate sketch is not a road map; a synthetic example is not operational delivery data. Input size ceilings are protective limits, not supported-service scalability claims.

A separately reviewed future progression is: (1) versioned asymmetric matrix input with directed arc costs, unit/type/provenance/date and unreachable-arc semantics; licensed road-distance/travel-time data kept outside the MVP, (2) directed objective/oracle/validator tests, without assuming route reversal preserves cost, and (3) native OR-Tools CVRP with explicit depot, vehicles, capacities and demands plus independent load/coverage checks. Time-dependent traffic and time windows require further specifications. The position-based TSP cost can mathematically use directed distances, but every affected schema, symmetry reduction, adapter and test must be revised before accepting them. Do not symmetrize a road matrix to fit Phase 1. CVRP has no promised general faithful QUBO conversion; unsupported quantum cases remain explicit. No extensions are implemented now.

## Typed domain contracts

Implement with strict Pydantic models, `extra=forbid`, finite numeric values, bounded collections and explicit `schema_version`. JSON round trips and generated TypeScript types must preserve discriminated unions. Schema version `1` is our versioned format, not an industry standard. Unknown versions fail explicitly; no implicit coercion of strings/bools into numeric fields.

| Model | Fields and semantics |
| --- | --- |
| `TspInstance` | `schema_version: Literal[1]`, `kind: Literal['tsp']`, `instance_id: str`, `city_ids: list[str]` (unique, input order authoritative), `depot_id: str`, `distance_unit: str`, `geometry: CoordinatesInput | MatrixInput`. |
| `CoordinatesInput` | `kind: Literal['coordinates']`, `points: list[{city_id: str, x: finite float, y: finite float}]`, `metric: Literal['euclidean_2d']`. Exactly one point per city. Planar coordinates in the stated unit; no latitude/longitude interpretation. Materialize symmetric distances with zero diagonal and persist them. |
| `MatrixInput` | `kind: Literal['matrix']`, `distances: list[list[finite nonnegative float]]`. Square matrix in city order, exact zero diagonal and symmetry; reject asymmetric data instead of silently averaging. Zero distances between different cities allowed; triangle inequality not required. |
| `TspAssignment` | `tour: list[str]` of length `n+1`, starts/ends at specified depot, every city exactly once before closure. Route reversal is permitted. |
| `TimetableInstance` (Phase 2) | Version/kind/ID, `rooms: list[Room]`, `slots: list[Slot]`, `lecturer_ids: list[str]`, `cohort_ids: list[str]`, `courses: list[Course]`, `preferences: list[Preference]`. All IDs unique within type and references checked. |
| `Room`, `Slot` | Room: `id: str`, `capacity: nonnegative int`. Slot: `id: str`, `label: str`, `order: nonnegative int` unique. Discrete slots do not overlap; no calendar/timezone inference. |
| `Course` | `id: str`, `lecturer_id: str`, `cohort_ids: list[str]` unique, `enrollment: positive int`. Exactly one single-slot meeting per course in B1; repeated meetings must be distinct course-event IDs. |
| `Preference` | `course_id: str`, `room_id: str`, `slot_id: str`, `penalty: nonnegative int`; unique triple, missing triples cost zero. Sum assignment penalties; avoid unspecified preference semantics. |
| `TimetableAssignment` | `assignments: list[{course_id, room_id, slot_id}]`; exactly one per course. Capacity, room, lecturer and intersecting-cohort collisions validated independently. |
| `SolveOptions` | `method: Literal['classical','quantum_local']`, optional compatible `solver_id`, `seed: bounded int`, `timeout_s: positive finite float`; quantum settings bounded `shots`, `reps`, optimizer evaluations, transpiler seed/optimization level. Defaults selected server-side and echoed. No QPU method in Phase 1. |

Proposed server ceilings: TSP input 4–200 cities, exact oracle at most 8 cities; QUBO compilation 4–8 cities; local quantum at most 16 variables, one worker, 60 seconds, 256 default shots per evaluation, `reps=1`, at most 50 objective evaluations. Compile acceptance does not imply execution acceptance. Upper request limits are protective design choices, not scalability claims; refine after measured Phase 1 resource tests. Timetable caps are set and tested in Phase 2 before enabling execution.

`Problem[I,A]` preserves all brief methods: `validate_input(I) -> Validated[I]`; `build_classical_model(Validated[I], solver_id) -> ClassicalModelHandle`; `to_qubo(Validated[I], EncodingOptions) -> QuboArtifact | Unsupported`; `decode_assignment(RawAssignment, DecodeContext) -> DecodeOutcome[A]`; `evaluate_original_objective(Validated[I], A) -> Objective`; `check_hard_constraints(Validated[I], A) -> ValidationReport`; `summarize_instance(Validated[I]) -> InstanceSummary`.

Classical handles are an internal typed union (exact route data, OR-Tools model, later CP-SAT model). Native SDK objects never cross JSON boundaries. Adapters return raw assignments/status/metadata. Only the verification service may promote a candidate to a feasible result. Decoding malformed candidates returns violations, never a guessed repaired assignment. A future repair heuristic must have its own method identity and timing.

## Result and error contract

`SolveResult` contains `schema_version`, `instance_id`, canonical `instance_hash`, `method`, `solver_id`, `solver_status` (native status also retained), `outcome` (`feasible | infeasible_candidate | no_solution | proven_infeasible | unsupported | resource_limit | timeout | error`), nullable typed `assignment`, `validation`, nullable `objective`, nullable `optimality`, `timings`, and `run_metadata`.

`ValidationReport`: `checked: bool`, `feasible: bool | null`, `violations: list[{code, entity_ids, message}]`. No candidate means `checked=false`, `feasible=null`; an invalid candidate means checked/false. `proven_infeasible` requires solver/oracle proof; failure to sample a valid bitstring is `no_solution` or `infeasible_candidate`. Preserve timeout plus a verified incumbent using separate solver status and outcome.

`Objective`: `value`, `unit`, `sense='minimize'`, `basis='original_problem'`. Publish only for feasible assignments; invalid diagnostics may separately include partial cost without ranking it as solution quality. `Optimality`: verified reference value/source, absolute gap and relative gap or null. Zero reference gives relative gap zero for a zero-cost feasible solution, otherwise null with reason. OR-Tools integer objective/bound is separately labeled and cannot prove optimality on the unrounded distances.

`Timings`: nonnegative measured seconds for validation, formulation, QUBO compilation, transpilation, solve (including QAOA optimizer loop), decode/verify, and total wall time; cloud network/queue nullable and not applicable locally. Define nonoverlapping stage intervals using a monotonic clock; user wall time includes applicable overhead. Null means unmeasured/not applicable, never fabricated zero. Record warmups separately.

`RunMetadata`: package/Python/Node/OS/architecture versions, seed and effective options, timestamps, instance/encoding hashes, lock digest, worker/thread limits, timeout/cancellation, simulator type, shots per call and total calls/shots, QAOA parameters/evaluations, transpiler settings, pre/post-transpile depth/gate counts, qubit count, target identity/calibration timestamp when applicable. Estimates have separate fields with assumptions. Peak memory is null unless actually measured. No tokens/account secrets.

For sampling, retain a count-weighted feasibility summary and candidate diagnostics; select the best **verified feasible original objective**, not lowest raw energy. Qiskit's library-selected optimum cannot bypass this service. Raw artifact retention is bounded and reproducible; failures and discarded invalid samples remain countable.

API: health, TSP solve, optional QUBO compile in Phase 1; timetable solve Phase 2; controlled comparison Phase 3. `classical` defaults to OR-Tools, with exact oracle explicit for tiny reference jobs. HTTP 422 handles invalid input; typed unsupported/resource-limit errors explain limits; disabled features return a stable error. Arbitrary uploaded QUBOs can be energy-inspected after schema validation but cannot produce a verified domain result without a matching original instance and registered decoder. Never import executable pickle/converter objects.

## QUBO convention and portability

Choose **upper-triangular** coefficients: `E(x)=offset + sum(i<=j) Q[i,j]*x[i]*x[j]`. Diagonal represents linear terms because `x²=x`. When starting from full symmetric `S`, canonicalize off-diagonal `Q[i,j]=S[i,j]+S[j,i]`; never double it again. Aggregate duplicate terms internally; exports contain unique sorted terms.

`QuboArtifact`: `schema_version=1`, `convention='upper_triangular'`, `sense='minimize'`, ordered `variables: list[{index,name,domain_ref}]`, `terms: list[{i,j,coefficient}]`, finite `offset`, `energy_unit`, positive `scale`, `source_instance_hash`, `encoding_id/version`, `penalties: list[{constraint_family,weight,adequacy_status,bound_basis}]`, `decode_map` (active indices, fixed variables, original IDs/order and auxiliary-variable mappings), and `provenance` (converter sequence/options/package versions).

Define scaling exactly: `E_export = scale * E_unscaled`, including offset and penalties; recover `E_unscaled=E_export/scale`. Default scale 1. Do not confuse this with OR-Tools distance rounding. Schema rejects unknown convention/version/encoder, nonfinite coefficients, out-of-range indices, duplicate variable names/indices/terms, lower-triangular terms, inconsistent dimensions and nonpositive scale. Decoding maps are invertible on feasible active domain assignments; slack encodings need not be globally bijective. Reconstruct fixed variables; validate auxiliary bounds and converter interpretation explicitly.

The explicit TSP polynomial is the independently testable reference and has no external converter dependency. After 1A, an isolated Mapper adapter may use [OptimizationProblemToQubo](https://qiskit.github.io/qiskit-addon-opt-mapper/stubs/qiskit_addon_opt_mapper.converters.OptimizationProblemToQubo.html) only for compatible inputs. Normalize ordering, coefficients, offset, scale, depot substitutions and penalties before comparing. Use the same constrained reduced formulation and explicit A to cross-check all 512 energies and route interpretation. Also compare Mapper's Ising operator plus its offset against the reference. A different automatic penalty must be tested against its own expanded expression and ground-state feasibility; its coefficients need not equal the explicit-A encoding. Extra auxiliary variables require a separately bounded full-space or auxiliary-minimization test, not a false nine-bit comparison.

Converter compatibility or `interpret` success is not domain feasibility. Preserve converter sequence/version/options and portable mapping; reject unsupported structures. Do not trust the library TSP application to choose the same reduction automatically. Archived Optimization may be a historical comparator only after these gates; it is not required. Import/export always requires the original model to claim feasibility.

## Encoding and verification

TSP: `x[i,t]` means city i at position t. Penalize both one-city-per-position and one-position-per-city with squared residuals; cost includes last-to-first edge. Fix depot at t=0, set other city bits at t=0 and depot bits at t>0 to zero, and substitute those constants **before** expansion. Active count `(n-1)^2`: n=4,5,6,8 needs 9,16,25,49 variables. The 4–8 scope supports formulation experiments; it does not promise full local QAOA execution for every size.

With nonnegative distances let `U=n*d_max`, a bound on any feasible tour. Every invalid binary active assignment violates at least one integer one-hot residual, giving penalty at least A. Choose `A>U` (e.g. `U+max(1,U)` in the stated distance unit). Raw cost remains nonnegative, so infeasible energy exceeds a feasible tour's upper bound. This is a proposed sufficient, conservative proof for this exact formulation, not an automatically valid bound for other converters or negative objectives. Guard finite arithmetic; test margins/tolerances and expose increased coefficient range. A deliberately weaker penalty is permitted only as an explicitly labeled experiment, with adequacy unproven and independent validation retained.

Timetable Phase 2: variables only for capacity-admissible `(course,room,slot)` triples. No admissible triple proves infeasibility for that course. One-hot course assignment, pairwise room/lecturer/cohort collision penalties, and linear soft preferences. Deduplicate conflict pairs. A conservative weight greater than the sum of maximum per-course soft costs separates invalid assignments from any feasible assignment when one exists; it does not establish that one exists. CP-SAT and bounded exhaustive enumeration check the same original constraints without QUBO.

Verification tests: compare expanded direct energy and canonical QUBO on all 512 assignments of reduced four-city TSP; all 65,536 assignments for selected five-city fixtures where tractable. Exhaustive routes (not all bits) for 4–6 cities establish original optima. Seeded random properties cover larger encodings. Test constant offsets, scale, fixed depot reconstruction, city-ID permutations, malformed samples, weak penalties, distance units and original objective round trips. Export/import must preserve energy and decoding. Test original validators independently using missing/duplicate cities and room/lecturer/cohort/capacity violations.

Ising uses `x_i=(1-Z_i)/2`; store resulting identity offset separately and test equality on every tiny basis state. [Qiskit bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering) requires explicit little-endian integer/string normalization and measurement-register/layout mapping. Test non-palindromic known strings; never use a visual bitstring as if its leftmost bit were variable zero.

OR-Tools routing uses integer arc costs ([official TSP guide](https://developers.google.com/optimization/routing/tsp)). Record scale s and nearest-integer policy, reject overflow, recompute returned distance on original floats. Each n-edge tour's rounding error is at most n/(2s); the ordering of near-ties may change. Even if an integer optimum were proven, this does not imply an exact float optimum. CP-SAT uses integers ([official guide](https://developers.google.com/optimization/cp/cp_solver)); B1 preferences are integer-valued.

## Mathematical checkpoint 1A contract

Use a concrete serialized four-city synthetic fixture, with depot A, city order `[A,B,C,D]`, unit `synthetic_cost`, and distance matrix:

```text
    A B C D
A   0 1 2 1
B   1 0 1 2
C   2 1 0 1
D   1 2 1 0
```

These are exact design inputs, not benchmark measurements or road distances. The analytical expected optimum is 4 via A-B-C-D-A or its reversal: every edge costs at least 1 and this four-edge tour attains 4. Approved Phase 1 implementation must independently enumerate all six depot-fixed routes and verify their sums without using the QUBO builder. OR-Tools then supplies a separately validated baseline; its status is not the proof of optimality. Do not execute these planned mathematical tests during this Phase 0 revision.

Define `y[i,t]` for i in `[B,C,D]`, t in `[1,2,3]`, index `3*city_rank+(t-1)` (city rank 0–2). Substitute fixed depot variables before expansion. Reference expressions:

```text
C(y) = sum_i d[A,i]*y[i,1] + sum_i d[i,A]*y[i,3]
       + sum_(t=1,2) sum_(i,j in B,C,D) d[i,j]*y[i,t]*y[j,t+1]
P(y) = sum_i (1-sum_t y[i,t])^2 + sum_t (1-sum_i y[i,t])^2
E(y) = C(y) + A_penalty*P(y)
```

For this fixture `U=4*2=8`; choose `A_penalty=16`, so every infeasible assignment has energy at least 16 while a feasible tour has cost at most 8. Expansion yields offset `6*A_penalty=96`. Each diagonal is `-2*A_penalty`, plus depot-edge linear costs at positions 1 and 3; each same-city or same-position distinct pair gets `2*A_penalty`, and consecutive-position pairs receive their tour-cost contribution once. Canonical upper-triangular evaluation includes offset. Direct row/column residual evaluation must be separately implemented, not call the coefficient builder under test. Design expectations are not passing-test claims.

Acceptance evidence must include all 512 records: ordered bit vector, direct cost, each residual/penalty, expanded coefficient energy including offset, feasibility and decode outcome. Exactly six permutation assignments should be feasible and 506 explicitly infeasible. Round-trip every feasible route; compare feasible costs to the independent route oracle. For invalid strings report missing/duplicate city/position violations; never repair by sorting selected bits. Demonstrate a deliberately inadequate weight (e.g. zero, where the all-zero string has energy zero but is invalid). A sufficient-weight global-minimum proof is separate from the behavior of a heuristic sampler.

Verify sign/sense, diagonal `x²=x`, off-diagonal factor, offset, penalty, scale round trip and depot map. For the integer fixture require exact equality; separately test float encodings with declared tolerances. Our vector index zero is the least-significant integer bit and the rightmost displayed bit; use `x0=1` alone -> `000000001` as an explicit non-palindromic case. Check classical `x=(1-z)/2` basis-energy algebra/identity offset without running a variational algorithm. SDK operator/register/layout compatibility tests occur in 1B. Store executed commands/versions and counts in the checkpoint report when actually run. Neither a QAOA optimum nor any feasible quantum sample is a 1A acceptance requirement.

## Quantum and IBM boundaries

Local path after 1A: validated domain -> reference QUBO -> reference or cross-checked Mapper Ising -> bounded QAOA -> raw samples -> decode -> original validator. [Mapper's official migration guide](https://qiskit.github.io/qiskit-addon-opt-mapper/how_tos/00_migrate_from_qiskit_optimization.html) separates mapping from quantum solving. Proposed execution uses [Qiskit `qaoa_ansatz`](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.qaoa_ansatz), [StatevectorSampler/V2 primitives](https://quantum.cloud.ibm.com/docs/en/api/qiskit/primitives), and [SciPy minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html) for a small bounded optimizer loop. This is the primary execution design, not a fallback contingent on trying unsupported Optimization first. Aer V2 remains optional after import/pass-manager checks. Compose established APIs without reimplementing a general optimizer/compiler; record actual sample outcomes and adapter identity.

Mapper is the preferred optional external mapping candidate, not a mathematical-checkpoint dependency. Its early pre-1.0 release, documentation/main mismatch and transitive dependencies require a published-release compatibility spike in 1B. The exact supported-release metadata is unresolved; inspected main's `qiskit<3` requirement must not be assumed to describe the release. [PRIOR_ART.md](PRIOR_ART.md) distinguishes official support from maturity/experimental-risk inference and compares all three options. A library disagreement blocks use of that adapter, not the independently verified core.

## Provisional research instrumentation

The penalty/feasibility/resource question in [PRIOR_ART.md](PRIOR_ART.md) is investigated only in approved later phases. Keep objective and each constraint-family polynomial separate so changing A does not change instance semantics. Record weight policy, adequacy proof/test status, coefficient range, normalization and raw sample violations alongside original quality. For a fixed formulation, nonzero penalty changes generally change weights/angles rather than variable count; log compiler target, seed, tolerance and structural cancellations before attributing gate/depth changes to A. Conversion-added slack/qubits are a separate formulation factor. TSP and B1 retain independent original validators and exact tiny oracles; never compare their incompatible raw objective units as a combined quality score.

For q statevector qubits, amplitudes alone require roughly `16*2^q` bytes in complex128, excluding workspace/copies/circuit overhead. At q=25 this is 512 MiB; q=49 is 8 PiB. These are analytical lower bounds, not measured memory. Default cap 16 is conservative pending RAM measurement; preflight all paths and terminate by deadline. No promise of Apple GPU/Metal/CUDA acceleration. A simulator executes classically.

IBM Phase 4 interface splits `prepare_resource_report` from `submit_authorized_job`; no submit capability in Phase 1. Dry-run against a recorded target is not a hardware run. Backend selection defaults classical; local quantum is research opt-in; cloud is disabled. Later server-side credentials, explicit instance selection, shot/time limits, approval and charge review are mandatory. Recheck evolving [IBM primitives](https://quantum.cloud.ibm.com/docs/en/guides/qiskit-runtime-primitives) and plan permissions then. Never automatically choose another paid instance when a job fails.

## Observed Mac and pending checks

| Observation (read-only commands) | Design consequence |
| --- | --- |
| macOS 26.5.2, build 25F84; `uname -m`: arm64 | Native Apple Silicon environment; exact CPU model and RAM unavailable. |
| Default Python `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3`, 3.14.5 | Do not use unqualified `python3` for project setup. |
| `/opt/homebrew/bin/python3.12`, 3.12.13, reports arm64 | Proposed project interpreter; native venv in Phase 1. No Python 3.11 found on PATH. |
| Node `/opt/homebrew/bin/node`, v25.9.0 | Present, but frontend compatibility untested; choose a supported LTS Node with Vite version at Phase 1 resolution. |
| `uv` and `pip-tools` not found in inspected environment | Proposed pip-tools hash locks; install only during approved Phase 1. A change to uv is acceptable if documented. |
| Xcode developer path `/Applications/Xcode.app/Contents/Developer` | Path exists; compiler/source-build ability not tested or required if wheels resolve. |
| Qiskit/Aer/Optimization/OR-Tools absent from inspected Python 3.12 distribution metadata | No runtime compatibility claim can be made. Other Python environments were not inventoried. |
| `sysctl -n hw.memsize` denied by sandbox | RAM and safe memory ceiling unresolved; keep 16-variable limit and require resource check before increasing it. |
| Only three root documents initially; `git status --short` failed: not a Git repository | No existing application, tests, manifest, lockfile, remote or Git history to preserve. |

[Qiskit installation/support docs](https://quantum.cloud.ibm.com/docs/en/guides/install-qiskit) list macOS arm64 as Tier 1 for 2.x. [Google's Mac guide](https://developers.google.com/optimization/install/python/pkg_mac) lists tested Ventura Intel/M1 systems; it does not certify this exact macOS version. Wheel evidence and candidate versions are in [PRIOR_ART.md](PRIOR_ART.md). Intel macOS wheels exist, but x86 support remains untested locally and needs separate CI evidence. Resolve transitive NumPy/SciPy/protobuf dependencies and execute real import/solve tests before declaring support. No Docker, paid account or source build is mandatory.

Unresolved environment facts: exact CPU/RAM/free disk, supported browser/Playwright installation, clean lock resolution on arm64 and Intel/Linux, chosen Node/Vite pairing, Mapper published-release/transitive-native compatibility and current core/Aer execution. Mapper was not installed or included in the earlier local metadata check. These checks do not block the design of 1A, which can avoid quantum dependencies; they must precede claims of execution support in 1B. IBM credentials/plan/device eligibility are intentionally unavailable and unnecessary for Phase 1.

## 1C implementation correspondence

No distributed workers, alternate problem semantics or quantum converter contract was introduced. The API calls the same classical dispatch as the CLI and the same 1B local runner; native quantum SDK imports remain inside the worker. `ApiResult` is a compact typed HTTP projection of those verified results; full exact permutation tables and full local traces remain research CLI artifacts. The generated OpenAPI/TypeScript schema is authoritative for HTTP field names. Total API compute work is measured from worker-service dispatch through cleanup/result construction; body reading, request-schema validation, HTTP serialization and browser/network time are not included. Uninstrumented stage times are not invented.

The proposed single-worker policy is implemented per server process: loopback, `--workers 1`, no queue, 503 on contention, cancellation/disconnect cleanup awaited before admission release. This is not a shared limit across replicas. Worker RSS is polled; parent payload/retention are bounded separately by 2 MiB input and a stricter HTTP quantum budget of 8,192 total requested shots. This additional combined cap protects HTTP trace decoding; it does not change the independent QUBO, solver behavior or existing research CLI bounds. A completed event followed by forced cleanup/nonzero exit is reported as `unclean_worker_exit`. Hard memory reservation, hard real-time scheduling and cleanup after abrupt parent/OS termination are not guaranteed.

Native Mac Node 24.22.0 LTS/npm 11.19.1, React 19.3.1/Vite 8.3.4 and TypeScript 5.9.3 were resolved; the generator is incompatible with the initially resolved TypeScript 7 API. Mac Chromium and in-app browser execution are recorded. Phase 0's observed environment table is historical; current package/lock/fresh-install/test evidence is in the report. Remote CI and other platforms/browsers remain unexecuted. License selection remains an owner-controlled release blocker.

### Targeted 1C corrections — 18 October 2026

The analytical sampling panel is fixture-specific and uses full structural comparison of the current parsed input against the unchanged original matrix preset. Other inputs receive a neutral unavailable-baseline statement; no computed/generalized baseline was added. Input edits remove previous results and stale tour sketches. Backend elapsed is explicitly computation/cleanup time, excluding HTTP/network/browser latency.

Additive diagnostic worker metadata measures `.start()` call duration and parent-observed first-event latency (which includes bootstrap/module imports/IPC/polling), native OR-Tools import, dispatch/validation/model work, native solve and cleanup. These are nested timing observations, not mutually exclusive benchmark stages. Solver settings/deadlines are unchanged. A bounded fresh-process investigation did not establish the cause of earlier failures; no major redesign or speculative reliability fix followed.

Review ZIP generation now takes committed project files only, explicitly requires hidden configuration and excludes Git internals/bundles, installed environments and untracked files. The external archive manifest hashes actual ZIP members including the embedded manifest; it does not assert that working-tree hashes alone prove archive completeness. Historical artifacts are immutable.


## Implemented Phase 2 B1 contracts and limits (18 October 2026)

`models/timetable.py` supplies strict input/assignment models, independent original feasibility and integer preference evaluation. `classical/timetable.py` supplies a room/slot exhaustive oracle and a separately constructed native CP-SAT model. `domains/timetable.py` implements all seven brief methods without changing the existing TSP protocol or introducing a universal IR. The CP-SAT model independently groups at-most-one room/lecturer/cohort constraints, with exactly one capacity-admissible placement per course. One native search worker, seed 1729 default, integer objective, no gap tolerance overrides. Native `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, `MODEL_INVALID` remain intact; best bound is nullable for infeasible/model-invalid. FEASIBLE/OPTIMAL candidates must pass original validation and objective equality with the native objective. UNKNOWN may retain the native numeric bound but no invented incumbent/proof. Enumeration OPTIMAL/INFEASIBLE describes exhaustive proof, not a CP-SAT run. Solver/model elapsed excludes lazy imports; API backend elapsed includes worker startup/imports/cleanup, excluding network/browser latency. Worker timing fields are nested, not disjoint stages to sum.

B1 limits are now explicit: at most 50 courses, 20 rooms, 40 slots, 50 lecturers/cohorts, 20,000 potential assignment cells/preferences; counts/capacity/cost/order bounded by 1,000,000; 256 candidate assignment rows (allowing invalid duplicates to be diagnosed without unbounded pairwise validation). Enumeration checks its <=65,536 original assignment product before expansion. QUBO compilation stops above 16 admissible variables and at most 136 upper-triangular coefficients. These are protective bounds, not performance promises. Shared supervisor/admission remains one active worker across domains, 60-second maximum whole-work budget, sampled RSS guard and cleanup diagnostics. The historical 20–30-second OR-Tools latency risk remains visible and unresolved.

`qubo/timetable.py` exports a distinct strict `TimetableQubo`: explicit schema/encoding version 1, B1 encoding ID, ordered variables with inline `(course_id,room_id,slot_id)` decoding map, unique canonical names, unique sorted upper-triangular terms, offset, whole-energy scale, source hash, penalty, soft bound, sufficiency flag, bound basis, units and explicit compiler provenance. No external converter is involved. Inline domain triples replace a redundant separately stored decode map; canonical recompilation must match the entire artifact before HTTP/CLI inspection. Domain-specific timetable compile/inspect endpoints preserve the original TSP artifact schema rather than forcing incompatible metadata into a universal artifact. B1 **display bits are index order left-to-right** and are expressly labeled; TSP MSB-first readouts remain unchanged.

With admissible variable groups `G_c` and deduplicated cross-course conflict pair set `P`, the unscaled expression is `sum_v preference_v*x_v + A*sum_c(sum_{v in G_c}x_v-1)^2 + A*sum_{(i,j) in P}x_i*x_j`. Expansion adds `-A` on group diagonals, `2A` on same-course pairs, `A` once on each conflict pair, and `A*course_count` offset. Scaling multiplies **all** terms and the offset. `U=sum_c max_{v in G_c}(preference_v)`, empty maximum zero; default `A=U+1`. For nonnegative costs every invalid bitstring costs at least A, while any feasible assignment costs at most U. This separation is conditional on feasibility; it cannot create it. Empty groups retain their constant penalty, including zero-variable artifacts. Lower custom A is supported only as explicitly insufficient mathematical inspection, never proof of ground-state feasibility. Zero-/multi-placement candidates retain their actual assignments and violations; no repair is performed.

`services/timetable.py` is the common validated classical dispatch used by CLI and API workers. `/api/problems/timetable/{solve,compile,inspect,validate}` use distinct strict schemas. The minimal `frontend/src/Timetable.tsx` editor/grid/inspection component uses generated OpenAPI types. Timetable `method` is classical only; QAOA remains the approved TSP path. No new B1 quantum execution, Ising/Mapper integration, benchmark suite or cloud adapter is implied. The mathematical fixtures are acceptance certificates, not Phase 3 experiments. Raw evidence and executed gates are in the implementation report.
