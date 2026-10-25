# Phase plan and acceptance gates

Current authorization (18 October 2026): targeted 1C corrections accepted; **Phase 2 B1 only** subsequently approved and now awaiting independent acceptance. Historical authorization notes below remain dated design records. No Phase 3–4 execution is authorized.

Revised 14 October 2026 after critical review. Architecture is provisionally accepted; **only Phase 0 document revisions are authorized**. The tasks below are executable plans, not work performed or approval to begin. Pause for user review after each phase and intermediate checkpoint under [PROJECT_BRIEF.md](../PROJECT_BRIEF.md) and the user's revised scope. No promised benchmark results or calendar-based success claims.

## Phase 0 — revised design, implementation authorization pending

1. Read the entire brief and root instruction files; inspect files and Git status.
2. Read current official Qiskit/Optimization/Aer, IBM Quantum Compute and OR-Tools references; review MQT and classical systems; distinguish established features from hypotheses.
3. Inspect local architecture/OS/interpreter/tool availability without changing the environment; record unavailable information.
4. Write only [PRIOR_ART.md](PRIOR_ART.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md) and this plan.
5. Investigate officially recommended Optimization Mapper, compare mapping/execution responsibilities and add targeted penalty/feasibility prior art.
6. Separate mathematical checkpoint from algorithm execution and product integration; reassess deadline workload and future road/CVRP boundary.
7. Check document completeness, local cross-links and scope boundaries; report changes and stop without starting Phase 1.

Acceptance: all four documents exist; actual primary URLs support research findings; Mapper comparison, all-512 mathematical checkpoint, research controls and future product boundaries are explicit. Original feasibility/objective checking, optional QUBO, credible classical baselines and Mac uncertainties remain binding. No application source, dependencies, lockfile, test scaffolding, cloud resources or benchmark data created. Architecture received provisional user review; revised checkpoint/dependency decisions and implementation authorization remain pending. A document audit is not software acceptance.

## Phase 1 — one complete TSP vertical slice (approval required)

Each row is a small reviewable task. Commit/review only tested changes once Git is initialized. Work sequentially through checkpoints; no timetable or IBM implementation. Passing a checkpoint does not imply authorization to start an unapproved next scope. Major frontend work is prohibited before the mathematical checkpoint.

### Checkpoint 1A — working mathematical core first

Essential before the first working checkpoint:

| Task | Concrete deliverable | Actual checks required before proceeding |
| --- | --- | --- |
| 1.1 Minimal Python environment | Initialize Git, Python 3.12 venv, minimal package metadata, Pydantic/OR-Tools/pytest and pinned hash lock; small test runner. | Clean local install/import and OR-Tools smoke solve. No FastAPI, Node, Qiskit, Aer or Mapper needed. Record Mac support honestly; full multi-platform certification follows later. |
| 1.2 Fixture/contracts/validator | Serialize the concrete synthetic four-city matrix in ARCHITECTURE, strict input/route/output models and original evaluator; stable city order/hash/units. | Input round trips; invalid/nonfinite/asymmetric matrix and duplicate/missing/depot cases; independent tour sums. Synthetic costs never labeled road distances. |
| 1.3 Independent classical optimum | Enumerate all six depot-fixed routes without QUBO; report original optimum and all tied tours. Add bounded OR-Tools baseline and original-cost validation. | Route sums agree with the independent lower-bound argument (analytical expected optimum 4); validate OR-Tools route against the same instance. OR-Tools success/energy does not certify optimality. |
| 1.4 Explicit QUBO/decoder/conventions | Nine active bits, depot substitution, cost and row/column penalties, strict canonical export/import, little-endian normalization and reference Ising basis algebra. | **Exhaust all 512 assignments**: direct polynomial versus coefficients plus offset, scale and Ising algebra; exactly six feasible/506 infeasible; all feasible route round trips; explicit invalid violations; sufficient A separation and weak-A counterexample. Test signs/diagonal/off-diagonal factors/non-palindromic bits. No converter or optimizer is the oracle. |
| 1.5 CLI and evidence package | Minimal solve/compile/inspect command path; versioned instance, route-oracle table, full 512 energy/feasibility table, schema/encoding map, tests and `IMPLEMENTATION_REPORT.md` checkpoint section. | Reproduce all artifacts from documented commands in locked environment; metadata and failures present; inspection rejects malformed assignments. Run the core tests and request 1A review before integration/frontend. |

**1A acceptance:** an actually executed four-city mathematical demonstration with independently verified optimum, independently computed all-bit energies, feasibility labels, encode/decode round trips and verified coefficient/offset/penalty/bit-order conventions. Required artifacts are produced only during approved Phase 1; the current design fixture's analytical expectations are not executed evidence. All mathematical tests must pass. QAOA installation, convergence, feasible sampling or optimum sampling are **not** acceptance conditions for 1A. No UI is necessary.

### Checkpoint 1B — mapping compatibility and local algorithm execution

After 1A review, when this scope is authorized:

| Task | Concrete deliverable | Actual checks required before proceeding |
| --- | --- | --- |
| 1.6 Direct core compatibility | Separate optional quantum lock; current Qiskit core/V2 sampler and SciPy; optional Aer; resource/time guard. | SDK operator plus offset equals all 512 reference energies; known bitstrings/register order; seeded local sampling; import/pass-manager and worker cleanup tests. No IBM service initialization. |
| 1.7 Optional Mapper cross-check | Time-box published-release metadata/installation check and reduced-model adapter; explicit penalty/order/offset normalization. | Compare every reduced energy and feasible decoding with 1A; verify Mapper Ising plus offset; test unsupported inputs. Record published release/commit, dependencies and incompatibility. If omitted/failing, keep direct core and document Mapper unvalidated; do not spend the deadline repairing upstream or require archived Optimization. |
| 1.8 Bounded four-city QAOA | Core `qaoa_ansatz`, bounded optimizer/sampler, measured metadata, candidate verification and quality relative to exact optimum. | Execute an actual run, validate all sampled candidates/counts, test no-feasible outcome, oversized rejection and timeout. Completion, feasible samples and optimal samples reported separately. Expand oracle to 4–6 cities, test rounding near-ties/overflow and broader seeded properties before final gate. |

**1B acceptance:** real bounded local execution through the verified mapping with recorded parameters/versions/resources. Mathematical correctness remains established by 1A, not by convergence. Report feasibility and original quality whether or not the optimizer finds the optimum; no artificial quantum success target or classical substitution. A run yielding no feasible candidate is a measured algorithm outcome, not a failed mathematical formulation if mapping tests pass. A crashing/unavailable backend is an unresolved integration failure. Record optional Mapper skip/failure distinctly. Review 1B before expanding product integration.

### Checkpoint 1C — minimal product slice and full Phase 1 gate

| Task | Concrete deliverable | Actual checks required before proceeding |
| --- | --- | --- |
| 1.9 API | FastAPI health/TSP solve/QUBO compile, shared CLI service, bounded worker, strict errors and loopback configuration. | Exact/OR-Tools/local integration; timeout/caps/cancellation; classical install without quantum dependencies; original validator mandatory. |
| 1.10 Small frontend | Supported Node/Vite pairing and lock; one preset, basic coordinate/matrix input, route sketch, units/metrics/violations and opt-in local quantum. | Vitest, complete preset Playwright flow, error/resource-limit flow and manual Mac/browser check. Generated API types and honest unavailable metrics. No elaborate editor/dashboard/map SDK. |
| 1.11 Final report/reproducibility | README/setup/limitations/license attribution, lint/format pre-commit checks, CI on available Linux/macOS runners, fixture artifacts and updated implementation report. | Fresh locked installation, full Python/frontend suites, documented real example and failures/skips; report actual platform coverage. Pause for full Phase 1 acceptance before Phase 2. |

Candidate setup uses `/opt/homebrew/bin/python3.12 -m venv .venv`; install pip-tools into that venv and compile hash locks per supported platform, then sync from the reviewed lock. This command is **planned, not executed**. Do not install globally or use unqualified Python 3.14 by accident. Versions from Phase 0 are resolution candidates, not approved compatibility pins. Obtain registry/network approval if sandbox tooling requires it.

Planned commands after implementation creates the relevant files: `.venv/bin/python -m pytest tests/unit tests/integration`, frontend `npm ci`, `npm run test -- --run`, `npm run build`, and `npx playwright test`; use pinned project dependencies and documented frontend working directory. CLI entry point should support `qws solve --instance examples/tsp/four_city.json --method classical --solver exact_tsp --output <path>` and an explicit `quantum_local` equivalent. Implement/document CLI flags before claiming these commands run. CI must not require paid accounts or IBM credentials.

Full Phase 1 acceptance requires **1A + 1B + 1C**, preserving the brief's complete four-city end-to-end slice, credible baselines, validated QUBO, actual local run with honest outcomes, tests/API/minimal UI, reproducibility and no practical speedup disclaimer. Six/eight-city quantum execution is not required. Mapper is an optional independently checked mapping candidate; archived Optimization is not required. Missing checkpoints must be listed, not renamed complete. If the user later authorizes only 1A, stop there; that is a legitimate rigorous partial deliverable, not full Phase 1.

### Workload and January 2027 application timeline

1A has five small essential tasks. 1B adds SDK/optimizer compatibility and process controls; 1C adds a separate frontend/toolchain and end-to-end testing. The latter two carry materially more integration risk and are not prerequisites to mathematical evidence. Do not give unsupported task-hour estimates or promise all phases by January.

Aim to freeze a reproducible admissions evidence package in December 2026, with review time before January; exact application deadlines are unknown. Protect 1A correctness first, then a small actual 1B experiment. If time is short, request scope revision to present those verified checkpoints with clearly listed unimplemented UI/timetabling/experiment work. Keep the original phase gates: this preference does not silently waive the full Phase 1 vertical slice before Phase 2. Optional archived comparisons, richer editors, broad benchmark grids and stronger platform claims can wait. Five-city full-bit tests are an optional expansion after 1A; all 512 four-city tests are mandatory.

## Phase 2 — B1 timetable (separate approval)

1. Implement typed single-slot course/room/lecturer/cohort inputs and independent validators. Test each hard violation and strict reference integrity.
2. Build first-class CP-SAT with integer soft penalties. Use a bounded exhaustive timetable enumerator as the tiny oracle; test proven feasible/infeasible fixtures, ties, optimum/bounds and timeout/UNKNOWN handling.
3. Compile only bounded capacity-admissible B1 QUBOs; document variable counts and penalty bounds. Exhaust tiny assignments; verify decode/energy/soft-objective round trips, deduplicated conflict pairs and weak-penalty failures. Cap larger cases and return unsupported/resource explanations.
4. Extend API/UI with timetable grid and concrete conflicts, then refactor shared interfaces only as justified. Run integration, Vitest/Playwright and manual UI checks.

Acceptance: CP-SAT results agree with tiny oracle on feasibility and optimal soft cost; QUBO candidates pass original validators or are violation-labeled; strict limits work; TSP regressions pass; implementation report updated. No hospital/industrial/general recurring scheduling claims. Pause for Phase 3 approval.

## Phase 3 — research design followed by separately approved implementation/runs

**24 October 2026 authorization:** the owner accepted Phase 2 with recorded limitations and approved **Phase 3A research/experiment design only**. No Phase 3 implementation or significant experiment is authorized. The older proposal below is superseded within this section; historical Phase 0/1/2 records elsewhere remain unchanged.

1. **3A (current, documentation only):** deepen primary-source review; audit actual execution paths; freeze a narrow falsifiable question, concrete semantic fixtures/reference expectations, seed/penalty/budget/normalization/compiler controls, raw artifact contracts, missingness/uncertainty rules and classical comparisons. Deliver [PHASE3_PRIOR_ART.md](PHASE3_PRIOR_ART.md), [PHASE3_EXPERIMENT_PROTOCOL.md](PHASE3_EXPERIMENT_PROTOCOL.md), [PHASE3_DECISION_GATE.md](PHASE3_DECISION_GATE.md). No application/benchmark code, dependency changes, new experiment results or B1 quantum adapter.
2. **3B-M (proposed, separate approval):** canonical explicit-artifact/penalty/normalization hook for current TSP runner; minimal B1 Ising/sampler research boundary with exhaustive SDK basis parity, non-palindromic bit/layout tests, caps, original validation and lifecycle regressions. B1 currently compiles/inspects QUBOs but its solve endpoint is classical only. Mapping-only approval does not authorize sampler calls; at most two specifically approved integration smoke calls are described in the decision gate. Stop for independent review.
3. **3B-E (proposed, separate approval):** implement bounded benchmark/artifact/start-ledger and analysis code, materialize and certify frozen fixtures with independent oracle/native reference/hash checks before study sampling, test raw-to-summary/missing-value/hash behavior. No significant batch from code approval alone.
4. **3C-R (proposed, separate approval):** run only a specifically approved frozen protocol/environment/allocation. Current design has four feasible tiny fixtures, 20 paired seeds, three penalty policies, negative controls, native classical and executed/analytical random references, <=9 study qubits and a four-hour software controller ceiling. Preserve every planned seed, failure, partial/no-feasible outcome, elapsed overhead and uncertainty; don't widen scope on favorable results. Stop for source/evidence review.
5. **3C review:** derive original-problem quality, feasibility and compiler/time results mechanically from artifacts; report replication/negative findings honestly, no asserted novelty gap or advantage. Any policy amendment, larger study, Phase 4/cloud work, public push/license/publication requires explicit owner approval.

**3A acceptance:** primary citations identify methods/resources/metrics and overlapping answers; the protocol distinguishes mathematical correctness, sampling, compilation and fair practical comparisons; B1 execution absence and TSP's missing penalty hook are explicit. Concrete fixtures, expected original optima/bitspace fractions, fixed settings, paired seeds, bounded work, missingness and uncertainty are specified prospectively. Source/evidence preserved, no claimed experiment execution. Ask for owner review before any 3B work.

Later experimental acceptance, if separately authorized: every number traceable to genuine raw artifacts; source/lock/fixture/compiler/seed provenance; credible native baselines; no energy-to-quality shortcut, absent-seed selection, simulated-to-QPU relabeling or queue-time-as-speedup claim. A coefficient change need not change circuit topology/depth. Null original objective for invalid/no-feasible/proven-infeasible cases stays explicit. A negative result or no novelty is legitimate; it does not authorize broad product ambitions. Phase 4 remains separately gated.

## Phase 4 — QPU research adapter and release (separate approval)

1. Revalidate IBM Compute primitives, package versions, plan/instance permissions and pricing. Build server-side credential boundary and offline/fake-target dry-run reports. Test disabled default, target compatibility, layout, no-secret logging and refusal without authorization.
2. Review a concrete transpiled circuit/resource report and expected charge assumptions with the user. **A Phase 4 development approval is not approval to submit a hardware job.** Credentials plus affirmative per-run authorization and charge review must precede submission. No resource purchase by default.
3. Only if authorized, perform a bounded run on the explicit instance; retain queue/network/QPU timing and metadata separately. Test cancellation/error/budget behavior; no automatic paid fallback. Without authorization, ship dry-run-only with hardware execution explicitly unvalidated.
4. Produce honest release/research report, reproducibility artifacts and license/dependency notices; test documented installation and inspect secret exclusion.

Acceptance: dry-run adapter reproducible and tested; any hardware claim linked to authorized real job evidence; skipped hardware clearly marked; no advantage/novelty claims inferred from job completion. CVRP, road maps, learned method selection and multiple QPUs remain separate future scope.

## Phase 0 execution record

Read-only shell commands executed (grouped for readability):

```text
cat PROJECT_BRIEF.md
pwd
rg --files -g '!**/.git/**' -g '!*lock*'
git status --short
uname -m
sw_vers
command -v python3
python3 --version
command -v node
node --version
cat AGENTS.md CODEX_START_PROMPT.md
command -v uv
command -v python3.12
command -v python3.11
xcode-select -p
sysctl -n hw.memsize
/opt/homebrew/bin/python3.12 --version
```

A read-only Python 3.12 snippet queried `platform.machine()` and distribution metadata for `qiskit`, `qiskit-aer`, `qiskit-optimization`, `ortools` and `pip-tools`. All five were absent in that interpreter. Documentation was read via web open/click/find/search calls; primary source links and fetch limitations are in PRIOR_ART. `apply_patch` created the four requested Markdown files. A final Python document audit checks files, Markdown fences, relative links and required design terms without adding application/test files.

Observed command failures: `git status --short` (not a Git repository), `sysctl -n hw.memsize` (operation not permitted), and missing PATH lookups for uv/Python 3.11. These are environment findings, not failing application tests. Package installation/import/solve and frontend tests were **not run** in Phase 0; no application/test suite exists. The Python document audit passed for all four files (headings, balanced fences, local links), all seven brief protocol methods and key format/environment terms, and the exact seven-file inventory (three existing root documents plus four new docs). No audit failures were observed. Git diff is unavailable until a repository is initialized. Only the four requested documents changed; existing root files were left intact.

## Phase 0 revision execution record

This revision used `cat PROJECT_BRIEF.md` (full brief), `cat` for the four design documents and a focused `cat docs/PHASE_PLAN.md`; `rg -n` inspected headings/dependency/task/timeline statements. Web tools read Mapper's official repository/docs/migration/API/release/installation pages, archived README, selected converter/Ising source and package metadata, plus targeted primary research sources. No dependencies were installed. `apply_patch` edited only the four requested documents. A read-only Python audit passed local links, fences and checkpoint/research/Mapper coverage, but its initial exact inventory assertion failed because a root `.DS_Store` now exists. This Finder metadata was left untouched; the corrected inventory check explicitly allows that one metadata file while still requiring exactly the seven project documents and no application files. Final audit results appear in the response. Fetch failures and release-metadata uncertainty are recorded in PRIOR_ART. No application/mathematical tests or quantum jobs were executed.

## Review items before starting Phase 1

Review the revised explicit-reference/optional-Mapper/core-execution boundaries and 1A/1B/1C checkpoints. Future authorization must specify 1A-only or full staged Phase 1; no implementation is authorized now. Resolve RAM/CPU information before increasing resource caps; license/Intel policy before release. Published Mapper metadata, native dependency compatibility, current SDK execution and later Node/Vite pairing remain untested. Stop after this Phase 0 revision.


## Phase 2 completion gate (18 October 2026)

Implementation covers tasks 2.1–2.4: strict original-domain checks; independently enumerated tiny proofs; CP-SAT native statuses/bounds with independently recomputed integer costs; <=16-variable optional B1 QUBO, sufficient/weak penalties, exhaustive certificates and canonical inspect; shared bounded API/CLI workers and a minimal React editor/grid/conflict view. Real FEASIBLE/UNKNOWN solver tests distinguish candidate quality from proof. TSP and local QAOA remain unchanged apart from module navigation/unmount cleanup. See the implementation report for final counts and authentic raw evidence, including initial test/tool failures.

Before accepting Phase 2, independently review the source archive/manifest, reproduce full Python regressions in the pinned optional environment, run the separate classical selection, build/Vitest/real Chromium flows, inspect all tiny energy/decoding rows, verify the original-domain proofs and all hidden configuration files. QUBO compile/inspect is the B1 quantum-compatible boundary; no B1 QAOA or cross-domain research experiment is claimed. The historical OR-Tools cold-start/tail-latency risk is still an acceptance limitation, not a repaired defect. Windows/Linux/Intel Mac and remote CI remain unexecuted here.

**Stop for independent Phase 2 acceptance.** Passing local gates does not authorize Phase 3, hardware, release, publication or a Git remote push. License choice remains blocked on explicit owner instruction before public release.
