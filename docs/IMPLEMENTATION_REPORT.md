# Checkpoint 1A implementation report

Date: 15 October 2026. Scope: user-approved tasks 1.1–1.5 only. **Checkpoint 1B and the rest of Phase 1 are not authorized.** Implementation, reproducible evidence and development/clean-install verification are complete. This is a mathematical checkpoint, not full Phase 1 product acceptance.

## Implemented scope and provenance

The user's project brief and reviewed Phase 0 design supply the direction, constraints and mathematical specification. Codex authored the Python implementation, tests, CLI, packaging and documentation. Independent human code review has not yet occurred. No practical quantum speedup demonstrated; novelty unverified.

Implemented strict Pydantic TSP/route/QUBO contracts, independent original-route validator/objective, exact depot-fixed permutation oracle, first-class OR-Tools routing baseline, explicit reduced city-by-position QUBO, independent direct residual evaluation, decoder/encoder and classical Ising basis algebra. The CLI supports classical solve, compile, inspect and checkpoint evidence generation. There is no QAOA, quantum SDK dependency, Mapper integration, hardware submission, frontend or API.

The four-city fixture is synthetic, with distance unit `synthetic_cost`. It is not a road matrix, delivery-routing service or fleet model. The original versioned format is our interoperable format, not an industry standard. Imported QUBOs are checked against the supplied original instance/registered encoder before decoding. Invalid candidates are violation-labeled and never receive a valid original-objective score.

## Mathematical evidence

The independent classical tests confirm all six depot-fixed permutations: B-C-D and D-C-B cost 4; B-D-C, C-B-D, C-D-B and D-B-C cost 6 (all tours start/end at A). A separate lower-bound argument gives four edges times minimum off-diagonal cost 1, so the cost-4 witnesses attain a global lower bound. OR-Tools independently returned a verified original cost of 4, but its heuristic result is not the optimality proof.

The explicit QUBO has nine active variables, city-major order B/C/D then positions 1/2/3; the depot is fixed and substituted. Upper-triangular coefficients are counted once; `x²=x` puts linear terms on the diagonal. Default A=16 exceeds U=8; constant offset is 96. All 512 parameterized tests compare unexpanded direct cost/residual penalties with coefficient-plus-offset energy and classical Ising-basis energy. They confirm six feasible permutations and 506 explicitly infeasible strings. Every valid route round-trips and is independently checked in the original problem. All-zero bits at A=0 have energy 0 and are correctly rejected as infeasible. Display `000000001` selects x0; the Ising convention is `z=1-2x` with separate identity offset.

Executed mathematical suite: **563 passed**, no failures, three OR-Tools SWIG deprecation warnings. Final development full suite: **568 passed, zero errors/failures/skips**, including CLI, artifact reproducibility and domain-boundary checks. The generated table shows exact equality of all 512 direct/QUBO/Ising energies, global minimum 4 and minimum infeasible energy 34. No quantum-algorithm success is inferred from these checks.

Clean locked `.venv-verify` full suite: **568 passed, zero errors/failures/skips**, three identical upstream warnings; [clean-install test XML](../evidence/checkpoint1a-clean-install-tests.xml). Development final pytest measured 1.30 seconds and clean-environment pytest 36.11 seconds; first-use import/environment overhead is included. These are raw single-run test-suite times, not solver performance comparisons. The warnings name `SwigPyPacked`, `SwigPyObject` and `swigvarlink` lacking `__module__` attributes.

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

Both editable installs and both `pip check` runs succeeded. The installed CLI generated evidence, solved the oracle, exported the QUBO and labeled `000000001` infeasible with energy 65 and no original objective. Generated mathematical tables reproduced byte-for-byte in two temporary runs during tests; timestamps and single-run timings intentionally differ. `pip-compile` warned about a future strip-extras default; pip also reported disabled sandbox cache/write access. These tooling warnings did not replace verification. Read-only Python/XML/hash audits and `git diff --check` supplement the commands above.

All network and protected Git mutations used the required approval mechanism. `git add` staged explicit project paths; meaningful milestone commits are listed below. No credentials, paid resource, cloud account or quantum package was used.

## Git milestones and changed files

- `a5130b8` — Add strict TSP models and independently verified classical oracle (24 passing classical tests at milestone).
- `4ee62b0` — Verify reduced TSP QUBO and decoding across all 512 assignments (563 passing tests at milestone).

New implementation files: `pyproject.toml`, `.gitignore`, `requirements/`, `examples/tsp/four_city.json`, `src/quantum_workload_studio/{models,classical,qubo,domains}/`, `cli.py`, `evidence.py`, and `tests/`. README, this report and generated evidence complete the review package. Original brief/instruction/Phase 0 documents were committed unchanged as the initial repository baseline. Dependencies/caches are ignored rather than committed. Final tested milestone commit title: `Complete checkpoint 1A CLI, locked environment and reproducible evidence`; obtain its hash from `git log` to avoid a report containing its own commit hash. No remote push occurred.

## Limitations and scope boundary

The hashed lock, clean locked installation, both full suites, installed CLI/evidence run and source/artifact hash audit have completed. No test failure or dependency incompatibility has been replaced with simulated evidence. Work stops at 1A for independent review; human acceptance of the implementation remains pending.

Exact oracle is capped at eight cities; ordinary inputs 4–200, QUBO 4–8, exhaustive evidence exactly four. These are protective bounds, not scalability evidence. Floating objectives use finite binary64 arithmetic; the integer fixture's comparisons are exact, while float property tests use relative 1e-12/absolute 1e-10 tolerances. OR-Tools rounds to integers with recorded scale/ties-to-even policy and recomputes original costs; it does not prove the optimum on arbitrary float distances. Timings are measured single runs, not benchmarks; seeds are not applicable to deterministic enumeration. SDK bit-order/operator execution, QAOA convergence, quantum resources, research benchmarks and timetabling remain unimplemented and unauthorized.
