# Prospective bounded penalty study — protocol 3A.1

24 October 2026. **Design freeze for owner review, not permission to run.** No new trial, benchmark implementation, adapter or fixture file was executed/created. Numerical fixture expectations below are either accepted historical certificates or explicitly identified hand-derived design values. Literature review: [PHASE3_PRIOR_ART.md](PHASE3_PRIOR_ART.md). Approval dependencies and implementation audit: [PHASE3_DECISION_GATE.md](PHASE3_DECISION_GATE.md).

## One question and its interpretation

**On the four fixed feasible fixtures below, does replacing the documented sufficient penalty A_ref with 4 A_ref change the paired-seed mean uniform-normalized feasible-shot fraction by at least 0.02, for p=1 X-mixer QAOA with the fixed normalization, 256 shots/evaluation and at most 16 evaluations?**

This is a small configuration-specific replication question; it is not a general penalty law, scientific novelty claim or quantum/classical advantage test. Both primary policies have provably feasible optimal ground states when the instance is feasible. A weaker policy is diagnostic, not another primary comparison. Results at this budget may be negative, mixed or inconclusive. No instance or seed will be selected after examining QAOA outcomes. Accepted 1B/1C/2 results have already been seen; this is a **prospective follow-on**, not a blind preregistration of those old acceptance runs.

Separate four layers:

1. **Mathematical adequacy:** original optimum and every tiny QUBO/Ising basis energy, including all ground-state ties. A sufficient bound proves a property of minimizers, not a heuristic probability.
2. **Sampling/quality:** feasibility over actual optimizer trace shots; original-objective quality only for feasible decoded assignments; optimizer convergence separately. Trace statistics are not final-parameter-distribution statistics.
3. **Circuit/compiler:** logical width, nonzero interactions, gate counts and depth at fixed p/target/compiler. Changing nonzero coefficients can leave every topology/depth count unchanged. Structural cancellation or bound-angle simplification is logged, not assumed.
4. **Practical classical comparison:** original quality/proof status and measured complete attempt time under equal maximum elapsed ceilings, with all overhead and tuning accounted. This study runs a classical simulator on a CPU; no physical quantum speed/cost conclusion follows.

## Frozen inputs and original references

Only the four feasible inputs T0, T1, B0, B1 enter the primary contrast. N0 and N1 are negative controls. No five-city/16-qubit expansion, random instance search, real road data, recurring classes or hidden instance filtering. These examples are intentionally tiny; they do not establish representative hardness.

### TSP inputs

Both use version 1, kind `tsp`, city order `[A,B,C,D]`, depot A, unit `synthetic_cost`, geometry kind `matrix`, exact symmetric integer costs interpreted by the existing finite-float schema. Assign distinct frozen IDs `p3a-tsp-T0` and `p3a-tsp-T1`; T0 is a **design copy** of the original matrix with a new ID, not a mutation of that file or its UI reference predicate.

```text
T0 = [[0,1,2,1], [1,0,1,2], [2,1,0,1], [1,2,1,0]]
T1 = [[0,1,7,2], [1,0,3,6], [7,3,0,4], [2,6,4,0]]
```

Depot-fixed order of permutations: BCD, BDC, CBD, CDB, DBC, DCB. Original cost vectors: T0 `[4,6,6,6,6,4]`; T1 `[10,18,18,18,18,10]`. T0 values are accepted Phase 1 evidence; T1 values are **hand-derived prospective expectations**, not a newly executed oracle result. T1 witness A-B-C-D-A costs 10. Original exact enumeration must independently agree before any T1 sampling; otherwise stop the study for a versioned correction.

| ID | Active bits / bitspace | Feasible assignments | Exact expected optimum / optimum count | Worst feasible cost | Uniform feasible / optimum probability | A_ref |
| --- | --- | --- | --- | --- | --- | --- |
| T0 | 9 / 512 | 6 | 4 / 2 | 6 | 6/512 / 2/512 | 16 |
| T1 | 9 / 512 | 6 | 10 / 2 | 18 | 6/512 / 2/512 | 56 |

For TSP, `U=n*d_max`, `A_ref=U+max(1,U)` exactly follows the accepted encoder: U=8/28 respectively. Both primary penalties are >U. No optimal-tour or feasible-permutation information enters quantum initialization/parameter optimization.

### B1 inputs

B0 is the complete content of [accepted tiny.json](../examples/timetable/tiny.json), copied prospectively with ID `p3a-b1-B0`. Room R1 capacity 30; slots S1/“Monday 09:00”/order 0 and S2/“Monday 10:00”/order 1; lecturer IDs `[L1]`, cohort IDs `[G1]`. Courses in order: Math (L1, G1, enrollment 20), Physics (L1, G1, enrollment 25). Preferences: Math/R1/S2=3, Physics/R1/S1=2, Physics/R1/S2=1; all other triples cost zero. Each course meets exactly once. The two feasible assignments cost 1 and 5, already verified in accepted Phase 2 artifacts.

B1 uses ID `p3a-b1-B1`, the same courses/slots/lecturer/cohort and room order `[R1,R2]`, both capacity 30. Full preference table (missing Math/R1/S1 means zero):

| Course | R1/S1 | R1/S2 | R2/S1 | R2/S2 |
| --- | --- | --- | --- | --- |
| Math | 0 | 3 | 2 | 5 |
| Physics | 2 | 1 | 4 | 3 |

This specifies every triple; future serialization includes only positive entries, in course → room → slot order. Shared lecturer/cohort forces different slots; two room choices for each course give 8 valid assignments. Math/S1 + Physics/S2 has costs `[1,3,3,5]` over room choices; the reversed slots have `[5,7,7,9]`. These are **hand-derived design expectations** and must be independently enumerated and CP-SAT-proven later. No B1 instance file or new measurement was produced now.

| ID | Active bits / bitspace | Feasible / optimum assignments | Expected optimum / worst feasible | Uniform feasible / optimum probability | U / A_ref |
| --- | --- | --- | --- | --- | --- |
| B0 | 4 / 16 | 2 / 1 | 1 / 5 | 2/16 / 1/16 | 5 / 6 |
| B1 | 8 / 256 | 8 / 1 | 1 / 9 | 8/256 / 1/256 | 9 / 10 |

B1 variable order remains course → admissible room → slot; conflict pairs are deduplicated across reasons. `U=sum_c maximum admissible preference`, `A_ref=U+1` as implemented. Expected feasible counts are checked from original assignments, not inferred solely from QUBO ground states.

### Negative controls

- **N0:** B0 with ID `p3a-b1-N0`, slots only S1/order 0 and **no preferences**. Two courses compete for one room, lecturer and cohort in one slot. Two active bits, four bitstrings, zero feasible assignments, U=0/A_ref=1, original optimum **null / proven infeasible**. Use only penalties 1 and 4. Every measured bitstring must remain violation-labeled; a nonzero feasible count is an implementation failure. Do not count absence of a solution as QAOA optimization success.
- **N1:** B0 with ID `p3a-b1-N1`, R1 capacity **0**, all original slots/preferences retained. No admissible variables. Original infeasibility is independently established; one empty-bit assignment, zero feasible assignments, U=0/A_ref=1, constant QUBO energy 2. **No QAOA run:** zero-qubit execution is explicitly unsupported, not a fallback success. Retain the preflight rejection plus mathematical certificate and native classical proof.

At later fixture-freeze implementation, validate strict models, serialize full JSON exactly, save canonical model hash and bytes SHA-256, validate independent oracle/CP-SAT references and all bitspace counts, then obtain review **before optimizer results**. Hashes of new fixtures are not invented here: complete semantic inputs are frozen above; materialized bytes/hashes are a later gate. Any discrepancy requires a new protocol version, never silent fixture editing.

## Weight policies and normalization

| Policy | T0 | T1 | B0 | B1 | N0 |
| --- | --- | --- | --- | --- | --- |
| Weak diagnostic | 4 | 14 | 1 | 2 | omitted (would duplicate 1) |
| Reference sufficient | 16 | 56 | 6 | 10 | 1 |
| Large sufficient | 64 | 224 | 24 | 40 | 4 |

The B1 diagnostic rule is `max(1,floor(A_ref/4))`, respecting the accepted integer-positive penalty schema; TSP uses A_ref/4. “Below conservative bound” is **not synonymous with inadequate**. For each policy certify whether all unconstrained minima are feasible and optimal, whether feasible/invalid minima tie, or whether an invalid minimum wins. Retain minimum invalid energy and all original-optimal/ground-state counts. A=0 can be an existing TSP mathematical counterexample only, not a new B1 feature or a sampled trial.

Keep portable QUBO artifact scale=1 and original cost units unchanged. From its unnormalized Ising `H_A + k_A I`, define `L_A=sum |nonidentity coefficients|` after exact zero aggregation; use `H_A/L_A` for phase evolution and sample-mean **E_A/L_A**, including k_A, for the optimizer. All study nonzero-bit fixtures must have L_A>0; otherwise stop. Record L_A, k_A and their scaled values. Offset is omitted from circuit evolution as global phase, never omitted from reported energy/parity checks. This is a **fixed policy-dependent normalization rule**, not an extra tuned treatment. It prevents arbitrary overall magnitude from being an undocumented angle-domain change; relative cost/penalty changes remain. Results apply to this normalization, not unnormalized QAOA generally. Gamma in original energy units is gamma_normalized/L_A.

## Frozen QAOA and compiler settings

| Item | Prospective setting |
| --- | --- |
| Sampler | Qiskit core `StatevectorSampler` V2, noiseless pure-state CPU simulation; no Aer/noise/QPU factor in this study |
| Ansatz | p=1; initial `|+>^q`; transverse-X mixer `sum X_i`; no custom mixer, warm start, repair, postselection objective, recursion or learned schedule |
| Optimizer | Locked SciPy COBYLA; at most 16 **function evaluations**, `rhobeg=0.5`, `tol=1e-3`, no f_target/early optimum shortcut; strict independent call guard |
| Loss | Count-weighted penalized sample mean E_A/L_A over **all** shots, including invalid ones; not original optimum or best feasible shot |
| Shots | 256/evaluation, <=4,096/trial; no separate final-parameter sampling in this protocol |
| Initial angles | NumPy default_rng(init_seed), two uniform draws in [0,2π), assigned by semantic parameter identity beta[0] then gamma[0]; record parameter objects/names and bound vectors; optimizer itself unbounded/no hidden wrapping |
| Compiler | Locked Qiskit, `qaoa_ansatz(..., reps=1, flatten=True)`; basis `[u,cx]`, all-to-all logical connectivity, optimization level 1, seed_transpiler=7; identity initial physical mapping/no device target or calibrations |
| Compilation measurement | Parameterized ansatz, with same measurement wiring, before numeric angle binding; save circuit hash and counts both before and after measurement, before/after transpile. Bind by Parameter object, not guessed vector order. |
| Resources | Main fixtures <=9 qubits; code guard <=16 (no study expansion). One owned spawned worker, one requested numerical thread, memory request 512 MiB subject to existing preflight/available-RAM check; one active job, no queue. |
| Deadlines | 20 seconds for whole attempt, including startup/imports/formulation/compile/sampling/verification, separate observed cleanup/reporting; native classical limit <=remaining wall budget. No automatic retries or deadline inflation. |

Official semantics checked during design: [StatevectorSampler V2](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorSampler), [ansatz](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.qaoa_ansatz), [COBYLA function-evaluation cap](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html). Retain accepted quantum/classical lock releases initially; record actual resolved environment at the later run gate. New SDK versions require a reviewed compatibility change before the study.

For each weight, extract h/J support and interaction graph before transpilation; log raw/scaled coefficient ranges, exact zeros and compiler tolerances. Compare counts on **parameterized** circuits, not different optimized angles. Do not claim more A implies more gates. Repeated post-binding counts are outside the primary compiler comparison. There are 14 nonzero-bit fixture/weight circuits, each compiled in one warmup and 20 trials; repeated timings are process/compiler observations, not independent topology samples or actual QPU resources.

## Seeds, trial order, warmups and classical comparators

Twenty paired seed blocks k=0…19, no selected/omitted “bad seeds”:

- Initialization seed `1000+k`; sampler evaluation e uses `100000+100*k+e`, e=0…15. Same initialization and sampler-seed sequence for every weight/fixture in block k, with disjoint reserved warmup seeds. Pairing supplies common pseudorandom numbers, **not identical samples** under differing circuits or guaranteed backend-independent coupling.
- Native CP-SAT seed `2000+k`, one worker. OR-Tools routing adapter and exact enumerators have no exposed stochastic seed: record null/not applicable, not a fabricated paired RNG setting.
- Executed uniform-bit comparator seed `3000+k`, 4,096 independent bit vectors per nonzero-bit fixture, original validator used, aggregate counts retained. Native solvers, not this weak comparator alone, establish practical context.
- Pair order balances elapsed/cache effects: four feasible fixtures ordered `[T0,T1,B0,B1]`, cyclically rotated by k modulo 4. Within a fixture, rotate method groups `[QAOA,original_oracle,native_solver,uniform_bits]` by k modulo 4; QAOA runs all three policies in `[weak,reference,large]` order rotated by k modulo 3. Here original_oracle is exact TSP enumeration or B1 original enumeration, and native_solver is OR-Tools routing or CP-SAT. Run N0 afterward with the same rotated method groups, alternating its two QAOA policy orders by k parity. Finish each block with N1 original enumeration/CP-SAT, reversing that pair on odd k; N1 has no quantum/random group. Every method/condition is serial; no parallel solver contention is intentionally introduced. Seed order is k ascending.
- Before measured blocks, **one explicitly retained warmup per QAOA fixture/weight condition** (14 warmups, 4 evaluations ×64 shots), one per native solver/fixture (12), and one per executed uniform-bit fixture (5). Use init seed 900000, warmup sample seed 910000+100*condition_rank+e; CP-SAT warmup 920000, random-bit warmup 930000+fixture_rank. Warmup time/shots/failures are saved separately, not discarded or relabeled unmeasured. Warmup fixture order is T0,T1,B0,B1,N0,N1; per fixture run supported QAOA weights in the displayed grid order, then original oracle, native solver, uniform bits. No adaptive extra warmups.

All methods run in fresh supervised workers. Warmed parent/OS caches are not a warmed persistent worker or proven cold hardware state. Label first observed worker/import separately; do not purge caches or claim first-ever cold boot. Record per-trial stage observations and execution order. Historical 20–30-second OR-Tools latency remains unresolved; a slow first request is not proof of its cause. Pause on unexplained systematic guard failures rather than redesigning the worker inside a benchmark.

Native comparators use the same original instances:

- Each TSP: exact depot-fixed enumeration and existing OR-Tools PATH_CHEAPEST_ARC + GREEDY_DESCENT, scale 1000/ties-to-even, original-cost validation. All study distances are integers so this scaling does not change route rankings. Routing status is heuristic; only oracle enumeration proves optimum. The adapter has no best-bound certificate or RNG seed to invent.
- Each B1/control: independent exhaustive original room/slot enumerator and CP-SAT native formulation, integer preferences, one search worker/seed above; retain OPTIMAL/FEASIBLE/UNKNOWN/INFEASIBLE/MODEL_INVALID and bound only when meaningful. Never force the native solvers through a QUBO.
- Uniform-bit comparator: five nonzero-bit fixtures including N0. The **analytical** reference is F/2^q, optimum probability O/2^q and `1-(1-F/2^q)^N` for N independent uniform draws; these formulae are not executed samples or assumptions about QAOA. N1 has F=0/one empty assignment and no executed sampler.

Use the same 20-second maximum full attempt deadline for each method; if a native solver proves optimum early, record its actual early finish rather than burning the remainder. QAOA also has its 16-call cap; this is a joint time/evaluation-capped comparison, not a claim that all algorithms consumed equal time or optimized their full time budget. No algorithm restarts, extensive hyperparameter tuning, baseline down-tuning, cherry-picked reference solver or GPU advantage claim. Report actual time/quality Pareto points, both best feasible and proof status. The executed uniform-bit comparator uses the maximum 4,096-draw budget. If QAOA ends before 16 evaluations, its actual shot count is smaller: report that difference and additionally evaluate the analytical uniform expectation at the actual N; do not call those executed runs equal-shot. Even a truly equal-shot comparison against uniform bits is a sampling sanity reference, not a fair CPU-time comparison by itself. Unused classical time is not penalized.

Offline exhaustive certification/oracle construction is a separately measured shared dataset-preparation cost. During an attempt, include actual reference loading or any repeated oracle computation performed by the existing runner; never subtract it selectively. The oracle can supply verification/reference scalars only, not a candidate, seed state, optimizer hint, loss shortcut or early stopping signal. User-visible timing must distinguish this offline setup from online full attempt and prior historical nested timing fields.

## Outcomes, normalization and uncertainty

For each evaluation store raw shots S, feasible shots F, invalid shots S−F and original-optimal shots O. All received bitstrings are independently decoded/validated. Preserve malformed keys with raw payload and invalid/mapping diagnostics; do not silently drop, repair or convert a layout error into low algorithm quality.

Trial trace metrics:

- `p_trace=F_total/S_total` and `p_opt_trace=O_total/S_total` when S_total>0, across **all evaluations**; optimizer proposals are adaptive, so these are trace averages, not one fixed distribution. F/S is null if no shots arrived. Counts sum exactly; partial/error trials retain actual received counts.
- Primary normalized feasibility `l=(p_trace-f_uniform)/(1-f_uniform)` on feasible fixtures. It is zero at the uniform-bit rate and one at full feasibility; negative values are allowed. Do not pool raw cross-domain percentages without their different f_uniform. N0/N1 are excluded from primary effect and all “solution success” denominators.
- Trace-best **feasible original** cost; absolute gap to independently proven f*, and within-fixture gap `(best-f*)/(worst_feasible-f*)` where denominator positive. Relative gap `(best-f*)/f*` only for positive f*. No feasible sample means cost/gaps **null with reason**, never infinity, zero quality or missing row. Feasible-cost distribution is count-weighted and labeled conditional. Unconditional attempt optimum-hit and any-feasible indicators accompany it. No penalized-energy approximation ratio is a substitute.
- Native optimizer success/message/call count is separate from best solution and execution_status. MAXFUN does not mean converged, but can be a clean bounded experiment. A timed-out trial with a feasible incumbent remains timed out with a partial candidate.

Primary paired contrast: for each block k, take the equal-weight mean of `l(large)-l(reference)` over the four feasible fixtures; then mean the 20 block values. The inferential target is algorithm-seed variation **conditional on these four fixed fixtures**, not a distribution of timetabling/TSP problems. Report each fixture's 20 paired differences as well as the aggregate, median, IQR, min/max, paired mean and raw points.

Use 10,000 seed-block bootstrap resamples with fixed analysis seed 424242 for a two-sided percentile 95% interval; blocks retain all four fixtures/policies. With only 20 blocks this interval is approximate and may be unstable. Do not treat 4,096 adaptive shots or repeated compilations as independent trial replications. Shot/binomial intervals may be descriptive for an individual fixed circuit, not a confidence interval for the whole adaptive trace. No significance hunting across diagnostic policies.

Decision regions, frozen before execution: lower CI > +0.02 supports a material increase for large A; upper CI < −0.02 supports a material decrease; entire CI within [−0.02,+0.02] supports a small effect under this budget; otherwise **inconclusive**. These are prospective practical thresholds, not a power guarantee or a claim of exact equivalence. Weak-policy, gap, optimum-hit and compiler/timing findings are secondary descriptive outputs, without undisclosed multiple-testing selection.

If any primary pair lacks a completed, valid trace, do **not** silently make a complete-case confirmatory claim. Retain every scheduled cell and report completed-pair statistics explicitly exploratory. For sensitivity, missing p lies in [0,1], giving missing normalized l in `[−f_uniform/(1−f_uniform),1]`; report worst/best aggregate contrast bounds over all scheduled cells. A no-shot trial is missing sampling probability, not observed p=0. Separately report operational yield `feasible_received/4096_requested`, marking unexecuted shots as unused budget (not invalid measurements), execution failure/no-sample rates and time-censored attempts. Do not resume/reseed failed cells automatically or replace them with better seeds.

## Prospective raw artifact contract (design, not implemented schema code)

Use JSON with explicit schema/version and SHA-256 links; all collection sizes are bounded by the trial caps. Reject extra/unknown fields at implementation. No pickle, executable options, arbitrary remote paths, credentials or account IDs. Proposed record types:

| Record | Required fields / rules |
| --- | --- |
| Study manifest | protocol ID/hash, acceptance/source commit, all fixture bytes+canonical hashes, locked package hashes, planned methods/policies/seed list/order/warmups, analysis script hash (when implemented), owner approval scope, frozen-versus-exploratory labels |
| Fixture certificate | domain/schema ID, original input, original enumeration table/proof, native reference status/bound/cost, q/2^q, feasible/optimal counts and f*/worst, QUBO artifact/hash, penalty/scale/L/offset, all basis rows with independent reference/SDK expectation/error/tolerances; expected-vs-verified distinction |
| Planned cell | immutable trial ID, fixture/method/policy/block, init/sample/transpiler/native/random seeds (nullable/N/A), planned shots/calls/deadline/memory, order index; a row exists even if never launched |
| Trial start/end | UTC timestamp plus monotonic origin/durations, actual command/options/source/lock/package/CPU/RAM/OS provenance, simulator identity/noise mode, requested threads, execution status, candidate outcome, native solver/optimizer status, complete/partial/not_run/censored flags and reasons |
| Evaluation event | event sequence, evaluation index, semantic parameter names/values, raw register-count keys, logical-to-classical/physical layout and normalization map, expected/actual shots, sample RNG seed, independent decoded counts/violations/original costs, unscaled/scaled sample energy, receipt timestamp; retain invalid raw events on mapping failure |
| Compile record | parameterized circuit hash/serialized artifact reference, target connectivity/basis/no-calibration marker, compiler version/seed/level/options/tolerance, parameter order, pre/post counts/width/depth/2-qubit count, whether measurement included, h/J support/hash and coefficients before/after scaling |
| Trial summary | shots requested/received/feasible/invalid/optimal/unused, trace metrics, selected candidate event/bitstring/cost/validation, selection policy, f*/gap, native bound/proof, optimizer flag/message, failures; **best across trace** explicitly distinct from final parameters |
| Resource/timing | complete controller and service duration; separately measured nonoverlapping phases where instrumented, legacy nested observations identified as such; RSS polling interval/observed maximum/scope, modeled amplitude/workspace values with assumptions; deadline detection/overshoot, PID exit/forced cleanup/alive state; CPU/GPU/QPU categories |
| Aggregate | all planned trial IDs and exclusions/reasons, missingness table, counts and weights, per-seed/per-fixture values, bootstrap seed/resamples/interval, no-selected-seed declaration, outcome decision and limitations; manifest hashes every raw file before report generation |

Numeric fields must be finite or null with an explicit missing reason. Objective units cannot be pooled between domains. N0/N1 original optimum/gap are null because the original problem is infeasible. Not-started/timeout/memory/monitor-denied/cancelled/error/unclean-exit/cleanup-failed records persist, including the last complete event. A completed event followed by forced termination is not a clean successful run. Retain controller exit status and logs even if no valid trial JSON was finalized; an atomic start ledger makes absence visible. Do not generate plausible replacement counts/timings. Final reports are mechanically derived from raw artifacts with round-trip and sum/hash tests before release for review.

Money fields: actual cloud/QPU charges **not applicable; no service used**. CPU-energy and electricity cost are unmeasured, hence null; zero billed QPU use is not zero total computational cost. Hardware/QPU IDs, calibrations/queue/execution metrics are N/A, never simulator metrics relabeled as hardware observations.

## Work estimate, bounds and stop conditions

This is a proposed bounded study, **not an approved run allocation**:

- Four feasible fixtures ×3 policies ×20 seeds = **240** QAOA attempts; N0 ×2 ×20 = **40** negative-control attempts; N1 has no QAOA execution. Total **280**, <=4,480 optimizer calls / **1,146,880** measured-trial requested shots.
- Fourteen QAOA warmups add <=56 calls /3,584 shots. Twelve native solver/fixture configurations ×20 =240 native attempts, plus 12 warmups. Five executed uniform-bit configurations ×20 =100 attempts, plus five warmups. No warmup is part of the primary trial count. Total including warmups **651** guarded work units; uniform measurements are classical RNG draws, not quantum circuit shots.
- Mathematical certification covers 3,897 planned basis rows: 2 TSP×3×512 + B0×3×16 + B1×3×256 + N0×2×4 + N1×1. Cap total certification work at 120 seconds; stop on mismatch or overrun rather than silently weakening it. N1 uses classical constant-energy algebra, not a zero-qubit SDK claim.
- Amplitude storage lower bounds: 9 qubits 8,192 bytes; 8 qubits 4,096 bytes; 4 qubits 256 bytes. SDK/import/workspace dominates these tiny arrays; existing model adds a 256 MiB allowance/workspace multiplier and checks available RAM. 512 MiB RSS request is a software policy, not a hard reservation. CPU model/available RAM/free disk and current contention must be measured at future execution; no new environment performance survey occurred now.
- At 20 seconds plus nominal one-second cleanup per work unit, 651 units budget **13,671 seconds**; plus 120-second certificates is **3 h 49 min 51 s**, before controller/export overhead and OS overshoot. This is a pessimistic planning envelope, **not measured runtime or a hard bound**. Historical subsecond tiny acceptance runs suggest lower typical work, but no reliable expected-duration estimate is available. Global study-controller budget **4 hours**; stop launching before a remaining unit cannot fit, retain not_run cells, and report incomplete analysis if the budget expires. Do not claim all seeds finished merely because the global cap is reached.

Before a future batch, a separately approved compatibility smoke check may test parity, cleanup and artifact integrity; no optimizer hyperparameter search on study outcomes. If platform/API mismatch, inadequate memory monitoring, contradictory oracle values, layout ambiguity or repeated startup failures occurs, pause for review. Do not silently switch SDK, backend, mixer, normalization, penalty, fixtures, seed count or deadline. Any amendment receives a version/reason/time and owner review before affected runs; all old attempts remain. No five-city expansion, QPU/paid service, CVRP or new scheduling semantics follows automatically from this protocol.
