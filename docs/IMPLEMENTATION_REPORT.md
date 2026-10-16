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
