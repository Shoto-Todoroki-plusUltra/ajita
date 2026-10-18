# Phase 2 B1 classroom timetabling — independent acceptance requested

18 October 2026. The owner accepted the targeted 1C fixes and authorized **Phase 2 only**, using accepted source `2f66cdf` as the baseline. Codex authored this implementation; no independent acceptance of Phase 2 is claimed. No Phase 3 benchmarks, Phase 4/cloud QPU integration, paid jobs, CVRP, remote push, license selection or publication occurred. The historical reports below remain intact as dated records; their former authorization statements are superseded by the owner's later instructions.

## Implemented scope and mathematical evidence

B1 supports one single-slot event per course, room capacities, declared nonoverlapping discrete slots, lecturer/cohort conflicts and additive nonnegative integer preference penalties (missing triples cost zero). Strict schemas reject unknown/missing IDs, duplicate IDs/references/preference triples, malformed numeric values and extra fields. Original assignments retain invalid/missing/multiple-course placements as violations; original preference objective is only defined after independent feasibility validation. There is no recurrence, duration inference, hospital scheduling or individual sectioning.

The **first-class CP-SAT** solver uses capacity-admissible Boolean placements, exact-one-course and independently grouped at-most-one room/lecturer/cohort constraints. Its actual native status and best objective bound are retained. Native FEASIBLE is not optimality proof; UNKNOWN is not infeasibility proof. Candidates are checked against original constraints and the integer objective is recomputed independently and compared to the native value. A separate original-domain enumerator traverses all room/slot choices, including capacity-invalid choices; it does not reuse QUBO mapping/conflict construction. The native status contract follows [official OR-Tools documentation](https://developers.google.com/optimization/cp/cp_solver); the maintained scheduling examples also demonstrate [Boolean assignments and resource constraints](https://developers.google.com/optimization/scheduling/employee_scheduling). These established techniques are not claimed novel.

The explicit optional QUBO has <=16 capacity-admissible variables, with input course → room → slot ordering. It exports sorted unique upper-triangular terms, offset, whole-energy scale, variable-index/domain mapping, explicit schema/encoding version, source hash, penalty/bound/sufficiency metadata and implementation provenance. Imported artifacts must equal canonical recompilation before domain inspection. **B1 displayed bits are left-to-right index order**, expressly labeled and distinct from existing TSP/Qiskit MSB-first readouts. Deduplicated cross-course conflict pairs incur one penalty even when room, lecturer and cohort all clash. Default `A=U+1`, where U sums maximum admissible preference per course, separates any invalid energy (>=A) from any feasible energy (<=U) under nonnegative costs. This conditional bound does not prove that a feasible assignment exists. Weaker custom A is visibly insufficient and has a counterexample test. Empty course groups retain constant A; capacity-impossible zero-variable artifacts decode to missing-course violations. No repair or fabricated fallback occurs.

| Tiny certificate | Original exhaustive oracle / native CP-SAT | Exhaustive binary assignments |
| --- | --- | --- |
| Two courses, one room, two slots, shared lecturer/cohort | OPTIMAL, preference **1**, native bound **1**; other feasible ordering costs **5** | All **16**; exactly **2** feasible |
| Same resource competition, one slot | INFEASIBLE proof from both | All **4**; none feasible |
| Room capacity zero | INFEASIBLE proof from both | **1** empty-bit assignment; positive constant penalty, invalid |
| Two-slot instance with no preferences | OPTIMAL **0**, two tied feasible orders | All **16**; exactly **2** feasible |

[Raw certificates and summary](../evidence/phase2/mathematical-summary.json) include each input, mapping, coefficients, independent oracle/native result and every binary energy/decoded assignment/violation. Expanded/direct energy discrepancy is zero on these integer fixtures; absolute comparison tolerance **1e-12** is recorded. Scaling is additionally tested at 0.25, 1 and 7. Twelve deterministic generated small instances (seeds 0–11, up to eight bits/all 256 assignments each) cross-check CP-SAT, original oracle, direct expression, expanded energy and feasibility. These are property-style correctness tests, not a Phase 3 benchmark or Hypothesis claim. CP-SAT seed 1729 and one search worker are used for reproducible fixtures; the tiny original optimum is independent of native heuristics. Dedicated tests exercise actual native UNKNOWN and FEASIBLE statuses with controlled test settings, without promoting them to proofs.

## API, CLI and UI

`domains/timetable.py` implements all seven brief methods. The independent domain, classical and QUBO modules remain concrete; there is no speculative universal IR. The common B1 classical service is used by CLI/API workers. New endpoints are `/api/problems/timetable/{solve,compile,inspect,validate}` with distinct strict OpenAPI schemas; original TSP endpoints/artifacts are preserved. Timetable solve accepts **classical only**, CP-SAT default or explicit tiny enumeration. The API and CLI share the existing spawn supervisor, sampled RSS guard, whole-work deadline, terminate/kill cleanup and clean-exit distinction. All domain solves share the one-active-job admission gate. Native import timing is null for enumeration, not a fictitious OR-Tools measurement. Execution errors/timeouts remain distinct from candidate feasibility and proof.

The minimal React module includes editable JSON/preset, solver selection, grid only for independently verified assignments, original preference objective, native or exhaustive status/bound, proof flags and measured computation/model/solver timing. Optional QUBO inspection shows actual coefficients, bit order and concrete original conflict explanations. Edits clear previous grid/QUBO/candidate data. Switching modules aborts the component's pending request. No timetable QAOA, Ising/Mapper adapter, random sampling experiment or analytical sampling percentages are implemented or implied. Existing TSP preset-specific analytics and full local QAOA flows remain tested.

Protective caps: 50 courses, 20 rooms, 40 slots, 50 lecturers/cohorts, 20,000 assignment cells/preferences; integer capacity/cost/order <=1,000,000, positive enrollment <=1,000,000; candidate validation <=256 rows; enumeration <=65,536 original combinations; QUBO <=16 admissible variables/136 terms. API whole-work deadline <=60 seconds, memory request 64–1024 MiB, one worker/no queue. These are protective ceilings, not scalability guarantees. Local CLI uses the same supervisor with LocalOptions limits. Worker cleanup remains subject to OS scheduling; no absolute hard memory/deadline guarantee is claimed. Model/solver time includes Python construction and solver execution; native CP-SAT wall time is separately retained in options. Backend elapsed includes imports/startup/cleanup and excludes HTTP/network/browser latency. Nested worker intervals must not be summed as disjoint stages.

## Executed acceptance gates

| Actual Mac check | Final outcome and raw evidence |
| --- | --- |
| Full optional-quantum Python suite, all existing Phase 1 tests plus B1 | **1,186 passed**, zero failures/errors/skips, four existing warnings. [XML](../evidence/phase2/full-macos-quantum.xml), [log](../evidence/phase2/full-macos-quantum.log) |
| Classical selection with no Qiskit installed | **647 passed, 1 intentional Qiskit-only skip**, zero failures/errors, four warnings. [XML](../evidence/phase2/classical-macos.xml), [log](../evidence/phase2/classical-macos.log) |
| Targeted B1 mathematical/API/CLI/lifecycle | **61 passed**, including actual solver proof/incomplete statuses, invalid samples, guards, cancellation/disconnect, cross-domain concurrency and completed-then-forced-cleanup regression. [XML](../evidence/phase2/backend-final.xml) |
| Vitest components | **12 passed** (nine existing TSP regressions and three B1). [XML](../evidence/phase2/vitest.xml), [final log](../evidence/phase2/vitest-final.log) |
| Real Chromium / real loopback API | **11 passed**: four B1 plus all seven TSP/QAOA/invalid/no-feasible/timeout/cancellation/analytics flows. [XML](../evidence/phase2/playwright.xml), [final log](../evidence/phase2/playwright-final.log). No production success mocks. |
| TypeScript/Vite / quality / schema drift | Build, Ruff/format, OpenAPI export check and generated TypeScript comparison pass. [Build](../evidence/phase2/frontend-build-final.log), [quality](../evidence/phase2/quality-final.log) |
| Dependency consistency / historical preservation | Both `pip check` calls pass; **126/126** old tracked evidence/requirements files byte-identical to `2f66cdf`. [Audit](../evidence/phase2/environment-and-preservation.json) |

[Complete commands, failures and chronology](../evidence/phase2/commands.md); [machine-parsed final XML totals](../evidence/phase2/acceptance-summary.json). Standalone real CLI outputs for CP-SAT, enumeration, compile and feasible inspection are retained as `evidence/phase2/cli-*.json`. Initial failures retained: test decorator syntax collection error, test-only nonexistent helper import (two API failures), duplicate new test module basename collection error, sandbox loopback bind rejection. All were corrected/re-executed; no source behavior was weakened to make tests pass. Initial Ruff/Prettier findings were corrected. An inline environment audit used the wrong system interpreter and failed; a stray shell token also failed. Neither is counted as a successful check; the pinned audit script produced the committed environment report. Earlier successful intermediate results are explicitly historical. Existing Starlette/HTTPX and SWIG warnings remain visible. Deliberate worker error/timeout/memory test fixtures are fault injection only, never solver result sources.

Actual environment: native **macOS 26.5.2 (25F84), Darwin 25.5.0 arm64**, CPython **3.12.13**, OR-Tools **9.15.6755**, Pydantic **2.14.1**, FastAPI **0.143.2**, psutil **7.2.2**, pytest **9.1.1**; Node **24.22.0 LTS**, npm **11.19.1**, React **19.3.1**, Vite **8.3.4**, TypeScript **5.9.3**, Vitest **5.0.5**, Playwright **1.64.1**, Chromium **156.0.8078.4**. Optional environment retains Qiskit **2.5.2**, Aer **0.17.2**, SciPy **1.18.0**. [Package snapshots](../evidence/phase2/packages-quantum.json), [browser metadata](../evidence/phase2/browser-environment.json). All existing locks/package pins were reused unchanged; no fresh dependency install was performed in this phase. Prior locked-install evidence is preserved, not misrepresented as a new install. Credential-free CI selection now includes B1; it was not run on GitHub. Linux, Windows, Intel Mac, other Python/Node versions and Safari/Firefox are untested here.

The real [desktop grid](../evidence/phase2/timetable-grid.png) and [mobile layout](../evidence/phase2/timetable-mobile.png) were visually inspected; automated flows additionally assert visibility and no horizontal page overflow. This is screenshot inspection plus real automated browser interaction, not a claimed separate manual browser session.

## Remaining risks and review package

**The historical intermittent 20–30-second tiny OR-Tools cold-start/tail-latency risk remains unresolved. Its root cause has not been fixed or established.** Passing Phase 2 runs do not resolve it. The UI explicitly retains that warning; no timeout was increased as a fix. CP-SAT also runs through native import/bootstrap and the same OS supervisor, so it is not exempted by assumption. Sampled RSS can overshoot; termination/cleanup is software-bounded with scheduling limitations. CP-SAT optimality proof applies to the defined B1 integer model, not universal scheduling quality. No unsatisfiable-core explanation is claimed: infeasible results state proof, and invalid candidates expose their actual original conflicts. JSON editing is deliberately minimal.

Sanitized source package: `review-snapshots/phase2-source.zip`, exact external `.zip.manifest.json`, whole-ZIP `.zip.sha256` and embedded `ARCHIVE_MANIFEST.json`. Built from the final committed HEAD with `scripts/create_review_archive.py`, then verified against actual members/hashes/CRC, including `.gitignore`, `.github/workflows/checks.yml`, `.githooks/pre-commit`. All old evidence remains included unchanged. No Git internals, credentials, environments, modules, caches, `.tools`, archives or unrelated/untracked files are packaged. The initial untracked root `ARCHIVE_MANIFEST.json` remains untouched and excluded. The archive's own manifest is generated internally; it does not use that root file. Targeted marker scanning is not a universal secret-audit guarantee. Archive digest is supplied externally to avoid self-referential source/archive hashing.

[File inventory](../evidence/phase2/FILE_INVENTORY.md) identifies domain/solver/QUBO, API/CLI, UI/schema, tests and evidence; Git history contains small tested milestones. No remote push. License is still unchosen, hence unlicensed/unpublished pending explicit owner instruction. **Stop here: request independent Phase 2 acceptance before Phase 3.** No automatic continuation is authorized.

---

# Targeted 1C corrections and reliability review

18 October 2026. Scope: only the user's fixture-reference, sanitized-archive, cold-start audit and elapsed-label corrections. The original web/API slice is **provisionally accepted** by the user-reported independent review; these corrections await review. No Phase 2, QPU/cloud integration, CVRP or research benchmark began. No push/publication/license choice. Codex authored this patch; no independent review of it is claimed.

## Changes and regression evidence

- The nine-bit/512-assignment/six-feasible/two-cost-4 analytical panel now requires **full structural equality of the current parsed input with the complete unchanged original preset**, independent of JSON key order. `instance_id` alone cannot authorize it. Changed same-ID matrices, coordinates, five cities, invalid JSON and other nonmatching inputs receive: “No analytical uniform baseline has been calculated for the selected instance.” Editing clears prior results, sampled-shot figures and the previous tour sketch. No new baseline was inferred or simulated. Analytical expectation remains distinct from executed experiments.
- The elapsed label is now **Backend computation elapsed (including cleanup)**, with a visible qualifier excluding HTTP/network/browser latency. No end-to-end timing was invented.
- Existing worker supervision/solver options remain unchanged. Added measured startup/import/spawn/solve/cleanup diagnostic fields/events; failures retain the reached phases. This is instrumentation, **not a claimed root-cause fix**. No deadline was increased for this audit.
- `scripts/create_review_archive.py` builds committed source only, explicitly requires all three hidden configuration files, refuses Git internals/bundles, credentials markers/credential URLs, environments/modules/caches and unrelated untracked files. Its external manifest is derived from actual ZIP bytes and hashes **every member including the embedded manifest**; exact member set, each digest and ZIP CRC are verified. It also supplies a whole-ZIP SHA-256. Targeted credential checks are not a universal secret-audit claim.

The required `.gitignore`, `.github/workflows/checks.yml` and `.githooks/pre-commit` exist, are tracked and are unchanged from `4b93eed`. They also exist with matching hashes in the old ZIP retained on this Mac, `checkpoint1c-source-4b93eed.zip`. The provenance of the reviewer's copy is unavailable, so its omission is **unexplained**, not attributed to an invented history or cause. [Input audit](../evidence/checkpoint1c-corrections/archive-input-audit.json). The new archive has an exact external manifest; prior manifests remain frozen historical records and are not used to claim the new ZIP is complete. The new package contains **no Git history bundle or `.git` objects**, unlike the earlier package.

| Actual post-patch check | Result |
| --- | --- |
| Full pinned optional-quantum Python suite, including all 1A/1B math regressions, API and new archive/timing tests | **1,125 passed**, zero failures/errors/skips; three original SWIG warnings and Starlette/HTTPX deprecation. [XML](../evidence/checkpoint1c-corrections/python-full.xml) |
| Classical API/mathematical/archive selection without Qiskit | **589 passed, one intentional Qiskit-only skip**, zero failures/errors; same four warnings. [XML](../evidence/checkpoint1c-corrections/python-classical.xml) |
| Isolated pytest startup timing probes | **3 passed** with fixed 20-second deadlines. [XML](../evidence/checkpoint1c-corrections/pytest-isolated.xml) |
| Archive contract tests | **3 passed**: required dotfiles, exact members/hashes, tamper detection, forbidden paths. Included in full suite. [XML](../evidence/checkpoint1c-corrections/archive-tests.xml) |
| Vitest | **9 passed**, including unchanged preset, changed matrix with same ID, actual coordinate control, five-city matrix, stale-sample/sketch clearing and elapsed-label qualifier. [XML](../evidence/checkpoint1c-corrections/vitest.xml) |
| Real Mac Chromium against real API/Vite | **7 passed**, including prior flows and actual original-preset solve → edit same ID → solve changed matrix → coordinates → five-city solve; no incorrect analytical figures and no mocked production success. [XML](../evidence/checkpoint1c-corrections/playwright.xml), [screenshot](../evidence/checkpoint1c-corrections/baseline-neutral.png) |
| Build / quality / schema drift / package consistency | TypeScript/Vite build, Ruff/format, generated OpenAPI/TypeScript checks and both `pip check` commands passed. [Build log](../evidence/checkpoint1c-corrections/frontend-build.log). No dependency versions changed. |

Initial correction full suite passed 1,122 before the three archive tests were added; final full count above is authoritative. No required test failed during this correction run. Two patch-context attempts failed without changing files, a missing optional `.gitattributes` read returned an error, and initial Ruff import ordering was corrected; these tooling outcomes are recorded in [commands](../evidence/checkpoint1c-corrections/commands.md). Deliberate timeout/resource/error test cases are still genuine failures of those requested runs, not relabeled successful solves. All previous 1A/1B and initial 1C raw artifacts, XML, locks and historical failure records remain byte-for-byte unchanged.

## Bounded startup investigation — risk remains unresolved

Pinned `.venv-api` on actual **macOS 26.5.2/build 25F84, arm64, CPython 3.12.13**. FastAPI 0.143.2, Uvicorn 0.54.0, OR-Tools 9.15.6755 and the existing lock versions were reused. Browser stack remains Node 24.22.0/npm 11.19.1 and Chromium 156.0.8078.4. See [raw environment/measurements](../evidence/checkpoint1c-corrections/cold-start.json), [derived summary](../evidence/checkpoint1c-corrections/reliability-summary.json) and actual commands. No cache purge, dependency reinstall, algorithm tuning, native-library substitution or paid resources were used.

The sequential driver ran **three fresh API interpreter processes**, with a first request and a warmed-server second request each; **every request still starts a fresh worker**. Then it ran **three fresh standalone workers** outside ASGI/pytest. Startup cap 10 seconds, unchanged per-request/native solver cap **20 seconds**, HTTP cap 23 seconds and whole-audit cap 240 seconds. Server shutdown and owned worker cleanup were bounded and observed. The audit actually finished in ~2.75 seconds: six HTTP 200s, three completed standalone workers, all verified original cost 4, clean worker exits/no surviving workers in those results.

| Recorded interval (seconds) | Actual observation |
| --- | --- |
| First observed server spawn-to-health | 0.2355; subsequent fresh-server starts 0.1925 and 0.1900 |
| First server Uvicorn / API-module imports | 0.0547 / 0.1111; measured inside that new interpreter |
| First observed HTTP request | 0.5755 driver wall time; native OR-Tools import 0.4533; native solver 0.0052 |
| Warmed-server requests (each with fresh worker) | 0.1271–0.1284 driver wall time |
| `.start()` call across six requests | 0.0010–0.0102 |
| Parent-observed first worker event | 0.0706–0.0799; includes bootstrap/module imports/IPC/polling, not isolated OS spawn time |
| Native OR-Tools import across six requests | 0.0398–0.4533 |
| Native solve across six requests | 0.00064–0.00522 |
| Worker cleanup across six requests | 0.0105–0.0116 |
| Standalone worker total | 0.1238–0.1403 |
| Isolated pytest/TestClient service computation | 0.1245–0.2363; separate artifacts from full-suite probes |
| Full-regression pytest/TestClient service computation | 0.1271–0.1324 in latest recorded three cases |

These timings are **nested**, not additive disjoint stages. Driver wall includes local HTTP/client overhead; UI backend computation does not. Fresh processes are not proof of flushed OS/file caches or a first-ever Mac native import. The very first *observed request in this audit* is retained distinctly, not silently discarded as warmup. Isolated and full-regression pytest observations are separate; ordinary desktop scheduling and overlapping frontend checks are not claimed absent. The sample is too small to characterize tail reliability or establish causality.

**The historical 20–30-second timeouts were not reproduced, and their cause is not demonstrated.** A slower first native import in this run does not explain those historical failures. No speculative fix, larger timeout, hidden warmup, fallback, stress/benchmark grid or major redesign was attempted. Unexplained cold-start/tail-latency risk remains explicitly open for independent review. Polling-based memory/deadline enforcement still has the earlier documented OS/overshoot/abrupt-parent-death limitations. This is a bounded reliability investigation, not a Phase 3 research benchmark.

## Review package and stop gate

[Commands](../evidence/checkpoint1c-corrections/commands.md) and [changed-file inventory](../evidence/checkpoint1c-corrections/file-inventory.txt) accompany the new sanitized full-project ZIP. `scripts/create_review_archive.py` packages committed HEAD, not arbitrary working-tree files; `.zip.manifest.json` outside the ZIP covers the exact actual member set and includes the embedded manifest's hash. The external checksum/manifest and required-hidden-file entries must be checked after transfer. Installed tools, environments, credentials, unrelated files and Git internals/history are excluded; required source-controlled configuration is retained. The archive is local only. Source/test milestone: `60b4fb6`; final evidence/report commit appears in Git log and archive metadata. No new platform or remote CI execution is claimed. No license chosen; project remains unlicensed/unpublished.

**Stop here. Please review these corrections and the unresolved reliability risk before any separately authorized Phase 2 work.**

---

# Historical initial 1C, 1B and 1A reports

The following original records, including all failures, are retained. Their prior archive packaging and fixture-panel behavior are superseded by the targeted corrections above.

# Implementation report — checkpoint 1C

Executed 16 October 2026; final review/package 17 October 2026. Scope: **1C only, tasks 1.9–1.11**, separately authorized after user-reported external 1B source/artifact review. Implementation and local acceptance checks are complete; independent 1C review remains pending. Work stops here. No Phase 2 timetable, Phase 3 benchmark study, Phase 4 hardware, CVRP, publication or remote push was started. **Unlicensed/unpublished: an explicit owner license instruction is a public-release blocker.** No practical quantum speedup demonstrated; novelty unverified.

## Implemented slice and provenance

Codex authored the new API, UI, tests, scripts and integration changes under the user's brief/design direction. The external reviewers' 1A/1B checks are user-reported, not represented as checks performed by Codex. Their missing Qiskit/OR-Tools environments did not cause source behavior changes. This checkpoint reused the original domain validators, canonical encoder, classical adapters and local V2 runner. Original 1A/1B tests, raw evidence, Mac XML and locks are byte-for-byte preserved; 1C adds separate evidence. Old manifests describe historical checkpoint sources, reconstructed from their commits; current modified CLI/worker and new sources are fingerprinted in the 1C manifest.

- `api/`: strict FastAPI health, exact/OR-Tools TSP solve, canonical QUBO compile/inspect, separately server-enabled local QAOA. No SDK import during API/classical startup, executable uploads or client paths. Generated OpenAPI and checked TypeScript models.
- `services/tsp.py`: shared classical dispatch used by CLI and API; classical jobs execute in spawned, supervised processes. Original objective/constraints remain authoritative. Full enumeration tables stay in research artifacts rather than HTTP responses.
- `execution/local.py`: seven-line lifecycle correction; a completed event followed by forced cleanup/nonzero exit becomes `unclean_worker_exit`. Existing 1B tests remain intact; new regression exercises the exact requested completed-then-hung sequence.
- `frontend/`: small React/Vite form, supplied four-city matrix, manually edited coordinate/matrix JSON, planar sketch, method choice and verified result. Matrix positions are schematic. Local quantum fields expose all evaluations' shots, weighted invalid/feasible fractions, best original cost across the entire trace, separate optimizer success, exact reference/gap and elapsed compute work. No final-parameter quality claim. Uniform reference is **analytical only**: six feasible and two optimal assignments out of 512, giving expected counts 48/16 for 4,096 independent draws; not an executed benchmark.
- Separate native classical API and optional quantum API hash locks; private npm package with pinned Node LTS/package lock; local lint/format/schema-drift hook. Credential-free Linux classical/frontend CI configuration is supplied but **has not run remotely**. No remote exists and no push was performed.

Architecture was checked against the Phase 0 documents before integration. No major domain/mapping/solver boundary changed. [ARCHITECTURE.md](ARCHITECTURE.md#1c-implementation-correspondence) records actual HTTP field/timing correspondence, per-process admission and a protective combined HTTP shot cap. The supplied UI does not implement a road/delivery service, geocoding, maps, accounts, external APIs, dashboards or future-domain placeholders.

## Actual Mac acceptance results

| Executed check | Outcome |
| --- | --- |
| Preserved 1B suite reproduced in original `.venv-quantum` | **1,103 passed; zero failures/errors/skips**; three original SWIG warnings. [XML](../evidence/checkpoint1c/reproduced-1b-1103-tests.xml) |
| Original 1A test files in classical API environment | **568 passed**, zero failures/errors/skips; three warnings. [XML](../evidence/checkpoint1c/original-1a-tests.xml) |
| Full `.venv-api-quantum` suite, all original regressions plus 16 API tests | **1,119 passed; zero failures/errors/skips**; three SWIG warnings plus Starlette/HTTPX deprecation. [XML](../evidence/checkpoint1c/full-quantum-api-tests.xml) |
| Fresh hash-installed `.venv-api-clean` classical/API suite | **583 passed; one intentional Qiskit-only skip**, zero failures/errors on latest run; four warnings. Qiskit absence verified. [XML](../evidence/checkpoint1c/fresh-classical-tests.xml) |
| Fresh offline `npm ci` from package lock | Passed; 136 packages installed; npm reported zero known vulnerabilities at execution time. Optional fsevents install-script warning retained; no script permission change. [Log](../evidence/checkpoint1c/fresh-npm-ci.log) |
| TypeScript/Vite production build | Passed. [Log](../evidence/checkpoint1c/frontend-build.log) |
| Vitest component/analytical/error checks | **4 passed**, zero failures/skips. Explicit test fixtures never feed application or measured E2E results. [XML](../evidence/checkpoint1c/vitest.xml) |
| Real macOS Chromium, real API/Vite servers | **6 passed**, zero failures/skips; classical and coordinates, QAOA, no-feasible, timeout, invalid/oversized, small viewport, cancellation/concurrency/recovery. [XML](../evidence/checkpoint1c/playwright.xml) |
| Ruff, new-file formatting, generated OpenAPI/TypeScript drift and Prettier | Passed; repository hook enabled and actually ran on the UI milestone commit. Historical mathematical core was not reformatted. |
| Manual Mac in-app browser | Actual OR-Tools and opt-in QAOA result controls/metrics verified; initial timeout also recorded. [Review](../evidence/checkpoint1c/manual-browser-review.md) |

Latest saved browser calls: exact original cost 4 in 0.1638 seconds service work; OR-Tools original cost 4 in 0.2524 seconds. Genuine StatevectorSampler QAOA p=1, seed 1729, 16 evaluations × 256 shots returned **61 feasible / 4,035 invalid of 4,096**, trace-best original cost **4**, exact reference **4**, gap **0**, optimizer success **false/MAXFUN**, elapsed **0.6799 seconds**. These are single acceptance runs, not comparative benchmarks or convergence/advantage evidence. The real four-evaluation, one-shot call produced **zero feasible / four invalid**, null route/cost/gap, execution completed and optimizer success false. Raw aggregated counts and effective settings are in the [browser response](../evidence/checkpoint1c/browser-quantum.json) and [no-feasible response](../evidence/checkpoint1c/browser-no-feasible.json). Every raw count was processed through the 1A decoder in the unchanged local runner; the response is a compact projection of that validation.

Worker tests cover timeout, cancellation, ASGI disconnect, handler-task cancellation, competing-job refusal, worker error, memory excess, unavailable monitoring, completed-then-hung workers and admission recovery. The browser test also starts genuine quantum work, observes 503 busy for competing work, cancels through the UI, waits for admission release and verifies a subsequent real exact solve. Injection is limited to clearly marked lifecycle test workers and unit presentation fixtures, never production success or measured route evidence.

## Guard policy and limitations

Single ASGI server process with **one active solve and no queue**; competing work returns structured 503. Always use loopback and `--workers 1`: the policy is not shared across replicas. The client cannot set paths, callables, providers or executable serialization. Strict extra-forbidden schemas, finite numeric fields, 2 MiB streamed-body cap, five-second body deadline, duplicate-key checks and local host/origin checks bound ingress. No public-service authentication/security/scalability claim is made.

Solver ceilings remain exact <=8 cities, OR-Tools <=200, QUBO <=8, local quantum <=16 variables, p<=2, <=50 evaluations, <=4096 shots/evaluation and <=60 seconds. The HTTP adapter additionally rejects requested shots × evaluations >8,192 before spawning to bound parent decoding/trace retention; research CLI limits are preserved. Top-level HTTP timeout/memory replace nested LocalOptions values and are echoed as effective options. API worker RSS budget defaults to 512 MiB and caps at 1024 MiB. RSS polling is worker-only; parent memory is bounded by payload/work caps, **not a kernel hard cap or reservation**. Poll/scheduling and per-event validation can overshoot; cleanup has bounded join attempts with terminate/kill, and a surviving worker is `cleanup_failed`. Successful event receipt alone is never successful execution.

Disconnect/cancellation signals the supervisor; admission stays occupied until cleanup returns. This does not guarantee cleanup following abrupt server/OS death, repeated interruption during shutdown, or uncontrollable OS scheduling. Only owned local workers, not arbitrary external processes, are supervised. There are no provider/cloud children. Total API service time runs from compute dispatch through worker/validation/cleanup/result construction; body parsing, HTTP request-model validation, network/browser latency and response serialization are outside that number. Unmeasured stage times are not fabricated. Quantum partial/no-sample results preserve `execution_status` independently of candidate outcome; clients must inspect it.

**Initial-delay limitation:** the first API test exceeded five seconds; after an explicit test-budget change to 30 seconds, a fresh classical run still timed out once (581 passed, one failure, one skip). Its [failed XML](../evidence/checkpoint1c/fresh-classical-initial-failure.xml) is preserved. A manual 20-second request also timed out visibly. Subsequent identical classical suite, full optional suite, browser flows and manual runs passed. A standalone import probe took ~0.172 seconds, and subsequent requests ~0.18–0.46 seconds. The cause of the earlier delays is **not established**; no kernel/library stack sample was obtained. No warmup, fallback or scope change hides them. Cold-start timing is not guaranteed; deadlines return real failures.

## Environment, failures and release status

Native macOS 26.5.2/arm64; CPython 3.12.13. FastAPI 0.143.2, Uvicorn 0.54.0, Starlette 1.8.0, HTTPX 0.28.1, psutil 7.2.2; original Pydantic 2.14.1/OR-Tools 9.15.6755 retained. Optional Qiskit 2.5.2/Aer 0.17.2/SciPy 1.18.0 retained. Fresh classical API hash install passed; quantum API lock was force-reinstalled in hash mode and `pip check` passed. Original environments/locks remain separate. [Classical metadata](../evidence/checkpoint1c/classical-environment.json), [quantum metadata/source hashes](../evidence/checkpoint1c/quantum-api-environment.json), [install logs](../evidence/checkpoint1c/fresh-classical-install.log).

Official Node **24.22.0 LTS**, bundled npm **11.19.1**, SHA-256 verified darwin-arm64 archive; system Node 25.9.0 unchanged. React 19.3.1, Vite 8.3.4, Vitest 5.0.5, Playwright 1.64.1, TypeScript 5.9.3, openapi-typescript 7.13.0; exact dependencies in npm lock. Initially resolved TypeScript 7.0.2 broke the generator's compiler API; its declared ^5.x peer range motivated the explicit compatible pin. Build errors for omitted generated request fields were corrected, not silenced. Browser version and actual architecture are in [browser metadata](../evidence/checkpoint1c/browser-environment.json); desktop/mobile screenshots are actual Chromium captures. No Safari, Firefox, Intel Mac, Linux or Python 3.11 certification. Remote CI remains unexecuted and must be verified after separately authorized remote setup/push.

[Development failures](../evidence/checkpoint1c/development-failures.json) also records the default pip-tools cache permission error, sandbox loopback-bind refusal, corrected diagnostic-tool errors, initial lint/build failures and warning/skip inventory. No final required local check is failing. Intentional quantum-only classical skips and remote/platform checks are explicit, not substituted by fake success. License selection and broader dependency-license review remain release blockers; no license was chosen. Imported dependencies retain their own licenses (e.g. Pydantic/FastAPI/React MIT, OR-Tools/Qiskit Apache, psutil BSD); no upstream code was copied into the new app beyond generated API types. The source snapshot excludes installed third-party runtimes/modules; dependency locks point to publisher packages.

Primary implementation references: [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/), [Playwright web servers](https://playwright.dev/docs/test-webserver), [OpenAPI TypeScript](https://openapi-ts.dev/introduction), [Vite requirements](https://vite.dev/guide/), [Node 24 archive](https://nodejs.org/dist/v24.22.0/) and [Node LTS policy](https://github.com/nodejs/Release). Runtime compatibility above is based on actual local execution, not documentation alone.

[Full executed commands](../evidence/checkpoint1c/commands.md), [changed-file inventory](../evidence/checkpoint1c/file-inventory.txt) and [artifact/source manifest](../evidence/checkpoint1c/manifest.json) form the review package. API milestone `81cb6d0`; UI/guard/quality milestone `7fc59f6`; final evidence/report commit identified by `git log`. The ignored `review-snapshots` ZIP is generated from that final Git commit, excludes pre-existing user `ajita.zip` and includes the tracked source/docs/tests/locks and all preserved evidence. Its separate checksum is returned with the ZIP, avoiding a self-referential tracked manifest. The user ZIP remains untouched and untracked. **Stop after 1C; independent review and separate approval are required before any later phase.**

---

# Historical 1B and 1A execution record

The following sections preserve their original completion records. Their former approval/human-review status is superseded by the user's subsequent reviews and separate 1C approval above.

# Implementation report — checkpoint 1B

15 October 2026. Authorized scope: tasks 1.6–1.8 only. **1C, Phase 2, cloud and product integration remain unauthorized.** The original 1A core/tests/artifacts/classical lock are unchanged. The user reported external review of that core and a reviewer-side OR-Tools limitation; no source behavior was changed to accommodate the review environment. Codex authored the new local adapter/tests/scripts. Independent human review of 1B remains pending. No practical quantum speedup or novelty demonstrated.

## 1B results

| Check | Actual outcome |
| --- | --- |
| Optional native environment | Qiskit 2.5.2, Aer 0.17.2, SciPy 1.18.0, psutil 7.2.2; separate hash lock, hash-verified reinstall and `pip check` passed. Classical environment unchanged. |
| SDK operator versus independent 1A reference | All 512 `Statevector.expectation_value(SparsePauliOp)` values plus identity offset match; maximum observed error 0, absolute tolerance 1e-10/relative 1e-12. QUBO offset is 96; Ising identity offset is 104. |
| Index/sign/layout | Tests cover x=(1-Z)/2, x0 at rightmost Pauli/display character, negative single-bit cost change, permuted logical/classical measurement wiring and reversed physical layout, with a non-palindromic feasible nine-bit fixture. Both V2 samplers pass. |
| Original 1A Mac suite | **568 passed, zero failures/errors/skips**, three upstream SWIG warnings; run in original `.venv`. |
| Full quantum-environment suite | **1,103 passed, zero failures/errors/skips**, same three SWIG warnings; includes all 1A tests, 512 SDK basis tests, lifecycle/invalid-sample/reproducibility checks, independent 4–6-city dynamic-program oracle comparison, five-city encoding properties and rounding diagnostics. |
| Mapper 0.1.0 | Separate environment; explicit A=16, same nine variables/order, canonical coefficients and QUBO constant match, all 512 energies/Ising expectations and six feasible assignments agree. No slack variables or automatic penalties. |

Controlled p=1, 16-evaluation, 256-shots/evaluation, seed-1729 experiments (transpiler seed 7, level 1, all-to-all `u/cx` basis):

| Local sampler | Raw shots | Feasible / invalid shots | Best feasible original cost / gap | Total recorded elapsed | Sampled worker RSS maximum |
| --- | --- | --- | --- | --- | --- |
| StatevectorSampler V2 | 4,096 | 61 / 4,035 (1.4893% / 98.5107%) | 4 / 0 | 0.7480 s | 123,240,448 bytes |
| Aer SamplerV2 | 4,096 | 54 / 4,042 (1.3184% / 98.6816%) | 4 / 0 | 0.5065 s | 127,926,272 bytes |

These are single local research runs, not performance benchmarks or evidence that one sampler is better. Each optimizer completed its specified budget; COBYLA's **success flag is false** because MAXFUN was reached, not convergence. Best feasible quality is selected from genuine shots across all optimization evaluations, not a classical fallback, repaired route or claim about the final parameter distribution. Every measured displayed key in every evaluation is decoded and independently original-validated, weighted by its observed count. Invalid shots remain in the denominator. No-feasible outcomes have null best objective/gap. The exact oracle supplies only the reference scalar. The full statevector repeat reproduced all raw counts, parameter paths and decoded outcomes exactly on this environment.

Compiled resource counts: nine logical/simulator qubits; pre-transpilation depth 18 with 30 RZZ terms; post-transpilation depth 49, 60 CX, 57 single-qubit `u`, nine measurements. These are circuit/compiler properties, not measured hardware resources. No device/noise model or calibration was used. Memory preflight's 8,192-byte state amplitude lower bound and ~256 MiB workspace/import allowance are analytical/modeled; the RSS column is a sampled process observation, not that model or an exact peak.

## Resource enforcement and honest failure reporting

One spawned worker per experiment; cap 16 variables, p<=2, 50 evaluations, 4096 shots/evaluation, 60 seconds. Preflight checks the modeled allocation against budget and budget against half observed available RAM. Imports/numerics use one requested thread; Aer is explicitly single-threaded. The parent checks elapsed time, cancellation and worker RSS with a 10ms polling wait plus per-event validation/OS scheduling latency; the maximum observed watchdog interval is recorded. Monitoring denial fails closed. Termination is followed by kill if necessary and bounded joins (0.25+0.75 seconds); tests verify no surviving worker. The total compute budget includes preflight/reference, spawn/import, compilation, sampling and original validation. Cleanup grace, report serialization and OS scheduling overhead are distinct; **these are software polling limits, not hard real-time or kernel hard memory caps**. RSS can overshoot between observations. Do not present sampled RSS as an exact peak or claim an absolute allocation guarantee.

[Worker probes](../evidence/checkpoint1b/worker-limits.json) record actual 0.01-second timeout and cancellation of the real worker, zero sampled candidates in those probes, no surviving workers and refusal of 25-variable input before allocation. Tests also exercise an uncooperative SIGTERM-ignoring worker, memory excess, unavailable monitoring, validation failure with raw event retention and injected worker error. Injected lifecycle targets are explicitly test fixtures, never experiment candidate sources. Timeout/error/cancelled execution is never relabeled successful because a feasible sample exists. No paid job, credentials, IBM Runtime, FastAPI, React, timetable or vehicle-routing implementation was used.

Observed development failures: initial operator-test fixture path was wrong (7 passed, 512 setup errors); fixed and rerun to 519 passing operator tests. Mapper's wheel-only dry-run failed on source-only Docplex; one 180-second install attempt permitting pure-Python source succeeded in 23.66 seconds. Its cross-check computation took ~0.26 seconds against a 30-second budget. Mapper was neither skipped nor substituted for direct-core solving. No Qiskit/Aer API breakage or unresolved failing test was observed. Previously recorded 1A tooling failures remain in the historical section below.

## Reproducibility, sources and review package

Exact commands are in [commands.md](../evidence/checkpoint1b/commands.md). Native locks: [quantum](../requirements/quantum-macos-arm64-py312.lock), [Mapper](../requirements/mapper-macos-arm64-py312.lock), plus exact Mapper snapshot. The Mapper lock includes hashed Docplex source; build tools are preinstalled/pinned and `--no-build-isolation` is required. Original classical lock/artifacts remain byte-for-byte unchanged. Mapper and quantum `pip check` passed; Mapper lock's offline hash-mode resolution was verified separately. All library versions in the actual run environments are saved in experiment provenance.

Primary current references: [Qiskit V2 primitives](https://quantum.cloud.ibm.com/docs/en/api/qiskit/primitives), [SparsePauliOp](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.SparsePauliOp), [qaoa_ansatz](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.qaoa_ansatz), [bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering), [Aer SamplerV2](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.primitives.SamplerV2.html), [SciPy COBYLA budget semantics](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html), [Mapper migration](https://qiskit.github.io/qiskit-addon-opt-mapper/how_tos/00_migrate_from_qiskit_optimization.html) and [converter API](https://qiskit.github.io/qiskit-addon-opt-mapper/stubs/qiskit_addon_opt_mapper.converters.OptimizationProblemToQubo.html). Initial SDK class URLs without the `qiskit.` prefix failed and were corrected. No archived Optimization package was installed.

Evidence: [512-state operator certificate](../evidence/checkpoint1b/operator-basis.json), [statevector run](../evidence/checkpoint1b/qaoa-statevector.json), [repeat](../evidence/checkpoint1b/qaoa-statevector-repeat.json), [Aer run](../evidence/checkpoint1b/qaoa-aer.json), [Mapper cross-check](../evidence/checkpoint1b/mapper-crosscheck.json), [full test XML](../evidence/checkpoint1b/full-quantum-environment-tests.xml), [original regressions XML](../evidence/checkpoint1b/1a-regressions.xml), [manifest](../evidence/checkpoint1b/manifest.json) and [file inventory](../evidence/checkpoint1b/file-inventory.txt). Run provenance includes source/lock hashes, seeds, options, every raw sampler count, circuit properties, timing, guard observations and optimizer termination. No claim of reproducibility on other platforms/releases is made.

Git milestone `7573898` locks/verifies environment and operator. The final tested local-execution/Mapper/report commit is identified by `git log` to avoid self-referential commit hashes. A pre-existing untracked `ajita.zip` was left untouched and is not committed. New code is confined to `execution/{operator,local}.py`, the research-only `local_cli.py`, supporting scripts and quantum tests; optional requirements, README/report and evidence were added/updated. Work stops for 1B review and explicit approval of 1C.

---

# Historical checkpoint 1A report

The following records the 1A completion state; its statement that 1B was unauthorized was subsequently superseded by the user's explicit 1B-only approval.

Date: 15 October 2026. Scope: user-approved tasks 1.1–1.5 only. **Checkpoint 1B and the rest of Phase 1 are not authorized.** Implementation, reproducible evidence and development/clean-install verification are complete. This is a mathematical checkpoint, not full Phase 1 product acceptance.

## Implemented scope and provenance

The user's project brief and reviewed Phase 0 design supply the direction, constraints and mathematical specification. Codex authored the Python implementation, tests, CLI, packaging and documentation. Independent human code review has not yet occurred. No practical quantum speedup demonstrated; novelty unverified.

Implemented strict Pydantic TSP/route/QUBO contracts, independent original-route validator/objective, exact depot-fixed permutation oracle, first-class OR-Tools routing baseline, explicit reduced city-by-position QUBO, independent direct residual evaluation, decoder/encoder and classical Ising basis algebra. The CLI supports classical solve, compile, inspect and checkpoint evidence generation. There is no QAOA, quantum SDK dependency, Mapper integration, hardware submission, frontend or API.

The four-city fixture is synthetic, with distance unit `synthetic_cost`. It is not a road matrix, delivery-routing service or fleet model. The original versioned format is our interoperable format, not an industry standard. Imported QUBOs are checked against the supplied original instance/registered encoder before decoding. Invalid candidates are violation-labeled and never receive a valid original-objective score.

## Mathematical evidence

The independent classical tests confirm all six depot-fixed permutations: B-C-D and D-C-B cost 4; B-D-C, C-B-D, C-D-B and D-B-C cost 6 (all tours start/end at A). A separate lower-bound argument gives four edges times minimum off-diagonal cost 1, so the cost-4 witnesses attain a global lower bound. OR-Tools independently returned a verified original cost of 4, but its heuristic result is not the optimality proof.

The explicit QUBO has nine active variables, city-major order B/C/D then positions 1/2/3; the depot is fixed and substituted. Upper-triangular coefficients are counted once; `x²=x` puts linear terms on the diagonal. Default A=16 exceeds U=8; constant offset is 96. All 512 parameterized tests compare unexpanded direct cost/residual penalties with coefficient-plus-offset energy and classical Ising-basis energy. They confirm six feasible permutations and 506 explicitly infeasible strings. Every valid route round-trips and is independently checked in the original problem. All-zero bits at A=0 have energy 0 and are correctly rejected as infeasible. Display `000000001` selects x0; the Ising convention is `z=1-2x` with separate identity offset.

Executed mathematical suite: **563 passed**, no failures, three OR-Tools SWIG deprecation warnings. Final development full suite: **568 passed, zero errors/failures/skips**, including CLI, artifact reproducibility and domain-boundary checks. The generated table shows exact equality of all 512 direct/QUBO/Ising energies, global minimum 4 and minimum infeasible energy 34. No quantum-algorithm success is inferred from these checks.

Clean locked `.venv-verify` full suite: **568 passed, zero errors/failures/skips**, three identical upstream warnings; [clean-install test XML](../evidence/checkpoint1a-clean-install-tests.xml). Initial full runs measured 1.30 seconds in development and 36.11 seconds in the clean environment, including first-use overhead. After the CSV correction, both full suites passed again: 1.13 and 1.01 seconds respectively; the linked XML files contain these latest runs. These are raw test-suite times, not solver performance comparisons. The warnings name `SwigPyPacked`, `SwigPyObject` and `swigvarlink` lacking `__module__` attributes.

Review artifacts: [summary](../evidence/checkpoint1a/summary.json), [512-row JSON table](../evidence/checkpoint1a/assignments.json), [CSV table](../evidence/checkpoint1a/assignments.csv), [six-route oracle](../evidence/checkpoint1a/routes.json), [OR-Tools result](../evidence/checkpoint1a/ortools.json), [QUBO](../evidence/checkpoint1a/qubo.json), [Ising basis polynomial](../evidence/checkpoint1a/ising_basis.json), [environment/source hashes](../evidence/checkpoint1a/environment.json), [artifact manifest](../evidence/checkpoint1a/manifest.json), and [development test XML](../evidence/checkpoint1a-tests.xml). The manifest covers 12 generated files; a separate audit verified every artifact digest, every recorded Python source digest and the lock digest. No Qiskit/quantum package is installed in the inspected environment.

## Actual environment and dependency resolution

- Native macOS 26.5.2, build 25F84, arm64; project CPython 3.12.13 at `/opt/homebrew/bin/python3.12`. Default system-selected Python 3.14 is not used.
- Downloaded classical-only dependencies into `.venv`: Pydantic 2.14.1, OR-Tools 9.15.6755, pytest 9.1.1 and pip-tools 7.6.2; transitive native packages included. `pip check` passed with no broken requirements.
- Sandbox DNS blocked the first dependency download; the approved network retry succeeded. Two all-platform hash-resolution attempts (one silent, one verbose/binary-only with bounded retries) were explicitly interrupted because they downloaded unrelated-platform wheels. The final pip-tools lock was generated successfully offline from the exact installed native wheel set, with unsafe build-tool pins included. No version was changed to hide a dependency conflict. The native lock installed successfully into a new `.venv-verify` using `--require-hashes`; no quantum packages were requested. Only this Mac's execution is claimed.
- Initial `git init` was denied by the `.git` write boundary; the approved retry initialized local `main`. No remote or publishing was configured. `ps` was denied in the sandbox; approved inspection confirmed the running lock process. Existing root `.DS_Store` is ignored and untouched.
- Exact CPU model, installed RAM and peak memory remain unmeasured. No Linux, Intel Mac or Python 3.11 execution/certification is claimed. License selection is unresolved before public release.

## Commands and outcomes

Repository inspection: full `cat PROJECT_BRIEF.md`, `cat AGENTS.md` and the four reviewed design docs, `rg --files`, `pwd`, `git status --short`; focused `sed` reads of mathematical/model contracts. `git status` initially reported that no repository existed. Official Pydantic strict-mode, OR-Tools TSP and pip-tools docs were rechecked using web tools.

Setup/execution so far:

```sh
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install pip-tools pydantic ortools pytest
git init -b main
.venv/bin/python -m pytest tests/test_classical.py -q
.venv/bin/python -m pytest tests/test_classical.py tests/test_qubo.py -q
.venv/bin/python -m pytest tests/test_cli.py -k 'not evidence' -q
.venv/bin/python -m compileall -q src
.venv/bin/python -m pip check
git diff --check
```

Outcomes: classical suite 24 passed; mathematical suite 563 passed; initial CLI selection 3 passed/1 deselected (evidence test awaited the lock, not declared passing); compileall, pip check and whitespace checks passed. All three pytest runs emitted the same three upstream SWIG deprecation warnings. No warnings were hidden. No failed mathematical tests have been observed. The interrupted lock attempt was an environment/tooling interruption, not a passing dependency-reproducibility check.

Lock commands (first two interrupted; final native-wheel path succeeded):

```sh
.venv/bin/pip-compile --generate-hashes --no-emit-index-url --no-emit-trusted-host --cache-dir /private/tmp/qws-pip-tools --output-file requirements/macos-arm64-py312.lock requirements/checkpoint1a.in
.venv/bin/pip-compile -v --allow-unsafe --generate-hashes --no-emit-index-url --no-emit-trusted-host --cache-dir /private/tmp/qws-pip-tools --pip-args '--only-binary=:all: --timeout=15 --retries=1' --output-file requirements/macos-arm64-py312.lock requirements/checkpoint1a.in
.venv/bin/python -m pip freeze --all > /private/tmp/qws-1a-resolved.txt
.venv/bin/python -m pip download --only-binary=:all: --dest /private/tmp/qws-1a-wheels -r /private/tmp/qws-1a-resolved.txt
.venv/bin/pip-compile --no-index --find-links /private/tmp/qws-1a-wheels --no-emit-options --allow-unsafe --generate-hashes --cache-dir /private/tmp/qws-native-lock --output-file requirements/macos-arm64-py312.lock requirements/checkpoint1a.in
/opt/homebrew/bin/python3.12 -m venv .venv-verify
.venv-verify/bin/python -m pip install --no-index --find-links /private/tmp/qws-1a-wheels --require-hashes -r requirements/macos-arm64-py312.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-verify/bin/python -m pip install --no-index --no-deps --no-build-isolation -e .
.venv/bin/python -m pytest -q --junitxml=evidence/checkpoint1a-tests.xml
.venv-verify/bin/python -m pytest -q --junitxml=evidence/checkpoint1a-clean-install-tests.xml
.venv/bin/qws evidence --instance examples/tsp/four_city.json --output evidence/checkpoint1a
.venv/bin/qws solve --instance examples/tsp/four_city.json --solver exact_tsp --output /private/tmp/qws-exact.json
.venv/bin/qws compile --instance examples/tsp/four_city.json --output /private/tmp/qws-compiled.json
.venv/bin/qws inspect --instance examples/tsp/four_city.json --qubo /private/tmp/qws-compiled.json --bits 000000001
.venv-verify/bin/python -m pip check
```

Both editable installs and both `pip check` runs succeeded. The installed CLI generated evidence, solved the oracle, exported the QUBO and labeled `000000001` infeasible with energy 65 and no original objective. Generated mathematical tables reproduced byte-for-byte in two temporary runs during tests; timestamps and single-run timings intentionally differ. `pip-compile` warned about a future strip-extras default; pip also reported disabled sandbox cache/write access. These tooling warnings did not replace verification. Read-only Python/XML/hash audits supplement the commands above.

The first final staged whitespace check flagged CSV CRLF endings. A combined shell command masked its nonzero exit, so commit `287f96c` was made before this was corrected. The exporter now explicitly writes LF, a regression assertion checks that byte convention, artifacts were regenerated, and both suites and the standalone staged whitespace check were rerun. This was a presentation/tooling failure, not a mathematical-test failure; no evidence values were hand-edited. The latest correction commit and refreshed XML are authoritative.

All network and protected Git mutations used the required approval mechanism. `git add` staged explicit project paths; meaningful milestone commits are listed below. No credentials, paid resource, cloud account or quantum package was used.

## Git milestones and changed files

- `a5130b8` — Add strict TSP models and independently verified classical oracle (24 passing classical tests at milestone).
- `4ee62b0` — Verify reduced TSP QUBO and decoding across all 512 assignments (563 passing tests at milestone).
- `287f96c` — Complete checkpoint 1A CLI, locked environment and reproducible evidence (both 568-test suites passed; subsequent CSV line-ending correction documented above).

New implementation files: `pyproject.toml`, `.gitignore`, `requirements/`, `examples/tsp/four_city.json`, `src/quantum_workload_studio/{models,classical,qubo,domains}/`, `cli.py`, `evidence.py`, and `tests/`. README, this report and generated evidence complete the review package. Original brief/instruction/Phase 0 documents were committed unchanged as the initial repository baseline. Dependencies/caches are ignored rather than committed. Final correction commit title: `Normalize evidence CSV line endings and refresh verified artifacts`; obtain its hash from `git log` to avoid a report containing its own commit hash. No remote push occurred.

## Limitations and scope boundary

The hashed lock, clean locked installation, both full suites, installed CLI/evidence run and source/artifact hash audit have completed. No test failure or dependency incompatibility has been replaced with simulated evidence. Work stops at 1A for independent review; human acceptance of the implementation remains pending.

Exact oracle is capped at eight cities; ordinary inputs 4–200, QUBO 4–8, exhaustive evidence exactly four. These are protective bounds, not scalability evidence. Floating objectives use finite binary64 arithmetic; the integer fixture's comparisons are exact, while float property tests use relative 1e-12/absolute 1e-10 tolerances. OR-Tools rounds to integers with recorded scale/ties-to-even policy and recomputes original costs; it does not prove the optimum on arbitrary float distances. Timings are measured single runs, not benchmarks; seeds are not applicable to deterministic enumeration. SDK bit-order/operator execution, QAOA convergence, quantum resources, research benchmarks and timetabling remain unimplemented and unauthorized.
