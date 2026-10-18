# Quantum Workload Studio

Checkpoints **1A, 1B and 1C** provide a locally usable symmetric TSP prototype: exact oracle, OR-Tools, verified optional QUBO, bounded local QAOA, FastAPI and a small React UI. No practical quantum speedup demonstrated; novelty unverified. Local quantum simulation executes classically. Work stops at 1C for review; later phases remain unauthorized. Unlicensed and unpublished: owner license instruction is required before public release.

This is a symmetric single-tour research example, **not a real-world delivery-routing service**. Coordinates are planar Euclidean distances. The four-city fixture uses synthetic costs, not road distances or travel times. See [the architecture](docs/ARCHITECTURE.md), [phase plan](docs/PHASE_PLAN.md) and [implementation report](docs/IMPLEMENTATION_REPORT.md) for scope, tests and limitations.

## Reproduce on the tested Mac

Target: native macOS arm64, CPython 3.12. The default `python3` on the development machine is 3.14, so select 3.12 explicitly. No Docker, IBM account or token is needed. The lock was resolved for this platform; Linux, Intel Mac and Python 3.11 are not certified by this checkpoint.

```sh
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements/macos-arm64-py312.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv/bin/python -m pytest -q
.venv/bin/qws evidence --instance examples/tsp/four_city.json --output evidence/checkpoint1a
```

The local editable package is installed from reviewed source; its third-party dependencies/build tooling are hash-locked. The lock includes testing/locking tools and no quantum dependencies. Open-source license selection remains the owner's decision before release; no license grant is invented here. This local checkpoint is not published to a package registry.

To rebuild the **same native-wheel lock**, download its hashed wheels into a local directory, then resolve the input against only that directory. The wheels are temporary, not committed; the lock is sufficient for a normal PyPI installation on the tested target. No other platform hashes are claimed.

```sh
.venv/bin/python -m pip download --only-binary=:all: --require-hashes -r requirements/macos-arm64-py312.lock --dest /tmp/qws-wheels
.venv/bin/pip-compile --no-index --find-links /tmp/qws-wheels --no-emit-options --allow-unsafe --generate-hashes --output-file requirements/macos-arm64-py312.lock requirements/checkpoint1a.in
```

The generation-command comment can differ by local wheel-directory path; dependency pins and SHA-256 hashes must agree. Updating dependency versions is a separate reviewed operation with fresh tests.


## Local API and UI (1C)

Use a separate classical API environment; it does **not** require Qiskit. The native Mac hash locks include test/build tools. Keep the earlier minimal classical and optional research environments if desired.

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api
.venv-api/bin/python -m pip install --require-hashes -r requirements/api-macos-arm64-py312.lock
.venv-api/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-api/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

In another terminal, use **Node 24.22.0 LTS with npm 11.19.1**, then:

```sh
node --version
npm --version
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. The version pins are in `frontend/.nvmrc`, `package.json` and `package-lock.json`; incompatible engines fail installation. The tested Node was the [official arm64 archive](https://nodejs.org/dist/v24.22.0/), SHA-256 checked before extraction; [toolchain evidence](evidence/checkpoint1c/node-toolchain.txt). The project-local `.tools` binaries and installed modules are intentionally excluded from Git/source snapshots. No system Node was changed.

For explicitly opt-in quantum mode, stop the classical server and use a distinct environment:

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api-quantum
.venv-api-quantum/bin/python -m pip install --require-hashes -r requirements/api-quantum-macos-arm64-py312.lock
.venv-api-quantum/bin/python -m pip install --no-deps --no-build-isolation -e .
QWS_ENABLE_LOCAL_QUANTUM=1 .venv-api-quantum/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Choose the supplied matrix, manually edit its JSON matrix/coordinates, or load the planar square example. Matrix drawing positions are schematic and do not define costs. Select OR-Tools, exact enumeration or opt-in local QAOA. No result is prefilled. Quantum fields show **all optimizer shots**, weighted feasible/invalid fractions, trace-best feasible original cost, exact reference/gap and a separately labeled optimizer success flag. A trace-best tour is not final-parameter distribution quality. The six-feasible/two-optimal-of-512 uniform calculation appears only when the current input structurally equals the complete unchanged original preset (not merely its ID). Otherwise it states that no analytical uniform baseline has been calculated. Editing clears previous results and sampling figures. The panel is an analytical expectation, excludes compute costs and is not an executed random/quantum benchmark. Backend computation elapsed includes cleanup but excludes HTTP/network/browser latency.

API paths: `GET /api/health`, `POST /api/problems/tsp/solve`, `POST /api/qubo/compile`, `POST /api/qubo/inspect`; contracts are in [OpenAPI](schemas/openapi.json). The solve body contains `instance`, `method`, classical `solver`, top-level `timeout_s`, `memory_limit_mb`, integer `scale` and optional `quantum` settings. **Top-level deadline/memory govern the entire job and replace the nested LocalOptions values**, which are echoed as effective settings. No file paths, serialized executables, accounts, network solver backends or arbitrary converter options are accepted.

One active solve per **single server process**, no queue; competing solves return structured 503 `busy`. Keep `--workers 1`; multiple server processes/replicas would each have their own admission gate and are unsupported. The UI uses Vite's same-origin `/api` proxy. Bind only to loopback; host/origin checks permit the documented local hosts/origins. This is not an authenticated public service. JSON is limited to 2 MiB and five seconds of body reading; duplicate keys, nonfinite values and extra fields fail. Exact mode caps at 8 cities, QUBO at 8, OR-Tools at 200 and local quantum at 16 active bits. API quantum work additionally caps **8,192 requested shots across all evaluations** to bound parent-side decoding/trace retention; the research CLI's original limits remain unchanged. The API uses only canonical explicit penalties for compilation.

Timeout, memory, cancellation and worker errors stay distinct from candidate quality. Classical execution failures return typed HTTP errors; quantum execution can return a result with a non-completed `execution_status` and any already validated samples. Inspect that status independently of `outcome`/cost. A completed message followed by forced termination/nonzero exit is `unclean_worker_exit`, not clean completion. Client disconnect or request cancellation signals cleanup, and admission remains occupied until the supervisor returns. RSS polling covers the worker; parent request parsing/retained trace are bounded by payload/shot caps, not a hard memory reservation. An abrupt server/OS kill cannot promise cleanup; there is no kernel hard memory or hard real-time guarantee.

Initial imports/requests intermittently exceeded supplied deadlines after fresh installation/reinstallation on this Mac; failures are preserved, and the cause is unproven. Later identical tests and manual flows passed. Retry only after checking the recorded status; there is no silent warmup/fallback or promise about cold-start latency.

### Checks and review package

```sh
.venv-api/bin/python -m pytest tests/api tests/test_classical.py tests/test_qubo.py tests/test_cli.py -q
.venv-api-quantum/bin/python -m pytest tests -q
.venv-api/bin/python scripts/export_openapi.py --check
npm --prefix frontend run types:check
npm --prefix frontend test
npm --prefix frontend run build
npx --prefix frontend playwright install chromium
# From frontend/ with Node LTS on PATH, both test servers stopped:
# npm run e2e
QWS_PYTHON=.venv-api/bin/python sh scripts/check_quality.sh
```

`npm run e2e` in `frontend` starts real loopback servers; its default optional interpreter is `.venv-api-quantum` and it requires Playwright's pinned Chromium. Set `PLAYWRIGHT_BROWSERS_PATH` consistently at browser installation/test time if using a project-local browser cache. Test responses and screenshots go to `evidence/checkpoint1c`; repeat runs overwrite those 1C files, **not** the preserved 1A/1B evidence. The original 1,103-test suite was reproduced separately at this gate. Classical installs intentionally skip the Qiskit-only API check; the full optional installation executes it.

[Actual commands](evidence/checkpoint1c/commands.md), [report](docs/IMPLEMENTATION_REPORT.md), [1C inventory](evidence/checkpoint1c/file-inventory.txt), [development failures](evidence/checkpoint1c/development-failures.json) and [manual review](evidence/checkpoint1c/manual-browser-review.md) distinguish real runs from unit-test fixtures. TypeScript models are generated from backend OpenAPI and checked for drift. Ruff checks new API/service code and the CLI; formatting checks scope to new code instead of rewriting the verified historical mathematical core. Pre-commit checks are supplied in `.githooks/pre-commit`; install with `git config core.hooksPath .githooks` and use the pinned Python/Node on PATH. The credential-free CI configuration has **not run remotely**: no remote/push is authorized. It targets Linux classical/frontend checks using pinned versions; Mac-only wheel hashes are not advertised as Linux hashes. Linux, Intel Mac, Python 3.11, Safari and Firefox remain untested. No timetable, comparative research benchmark, hardware execution or CVRP is included.

## CLI

```sh
.venv/bin/qws solve --instance examples/tsp/four_city.json --method classical --solver exact_tsp
.venv/bin/qws solve --instance examples/tsp/four_city.json --solver ortools_tsp --scale 1000 --timeout-s 1
.venv/bin/qws compile --instance examples/tsp/four_city.json --output /tmp/four_city_qubo.json
.venv/bin/qws inspect --instance examples/tsp/four_city.json --qubo /tmp/four_city_qubo.json --bits 100010001
.venv/bin/qws inspect --instance examples/tsp/four_city.json --qubo /tmp/four_city_qubo.json --bits 000000000
```

`solve` defaults to OR-Tools; `exact_tsp` explicitly enumerates original tours through at most 8 cities. Input supports 4–200 cities; QUBO compilation supports 4–8. These are protective bounds, not scalability promises. `evidence` requires exactly four cities to keep its exhaustive space at 512 assignments. Each command accepts `--output`; existing files in the selected output paths are overwritten. Errors exit 2 with structured stderr. Valid but infeasible bitstrings produce violations and a null original objective, never a repaired tour.

Our versioned QUBO format uses upper-triangular terms: `E=offset+sum(i<=j) Qij xi xj`. Linear terms occupy the diagonal; off-diagonal terms are counted once. Default penalty exceeds `n*d_max`. `--penalty 0` is allowed only as an explicitly unproven experiment. Scaling multiplies the whole energy including offset, with `unscaled=energy/scale`. Imported artifacts must match the original instance and registered encoder before decoding. This is our interoperable format, not an industry standard.

Bit vectors are city-major, nondepot city then positions 1..n-1. Integer bit zero is variable zero; displayed strings place it at the rightmost end. `000000001` selects only x0. The classical Ising basis transformation uses `x=(1-z)/2` and a separately retained identity offset; it does not execute a quantum algorithm.

## Evidence and review

[Checkpoint artifacts](evidence/checkpoint1a/summary.json) include the full 512-row JSON/CSV table, all six oracle routes, OR-Tools result, portable QUBO/schema, materialized distances, package/source/lock hashes and artifact manifest. Mathematical tables reproduce identically; timestamps and single-run timings vary. Measurements are not comparative benchmarks. Every decoded candidate is checked against original constraints before original-objective reporting.

Tests parameterize all 512 assignments independently, check the hand-tabulated routes and lower-bound proof, reject corrupt/malformed inputs/exports and exercise CLI behavior. [IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) records actual results and commands. The user reported external review of the 1A source/evidence; that reviewer lacked OR-Tools, so full Mac execution evidence remains separate. The user also reported independent review of 1B source/artifacts and separately approved 1C. Those reviewers lacked the complete local Qiskit/OR-Tools stack; the original Mac XML and raw evidence are preserved. 1C independent review is pending. Later phases require separate explicit approval.

## Optional checkpoint 1B local experiment

The classical environment and original CLI remain independent. Use the separate native Mac quantum lock (Qiskit 2.5.2, Aer 0.17.2, SciPy 1.18.0, psutil 7.2.2); no archived Optimization or IBM Runtime dependency is needed.

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-quantum
.venv-quantum/bin/python -m pip install --require-hashes -r requirements/quantum-macos-arm64-py312.lock
.venv-quantum/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-quantum/bin/python scripts/check_quantum_environment.py
.venv-quantum/bin/python -m pytest -q
.venv-quantum/bin/python -m quantum_workload_studio.local_cli --instance examples/tsp/four_city.json --output /tmp/qaoa.json --shots 256 --evaluations 16 --seed 1729 --timeout-s 60
```

`--backend aer` selects the separately tested Aer V2 sampler; otherwise the core StatevectorSampler V2 is used. This is a research CLI, not a product endpoint. The objective is the mean penalized energy across all shots. Output reports all evaluations and raw counts, count-weighted original feasibility, violations, best feasible original objective across the optimization history and gap against the exact oracle. It does not claim final-parameter quality or convergence from finding one good sample. Missing feasible samples produce a null best/gap. Execution errors, timeouts and cancellation stay distinct from solution quality. No classical fallback or repair can supply candidates.

Guards: at most 16 active variables, p<=2, 50 evaluations, 4096 shots/evaluation and 60 seconds. Preflight includes modeled statevector/workspace/import allowance and available RAM. The watchdog uses a 10ms polling wait, with additional per-event validation and OS scheduling latency; its largest observed interval is recorded. A spawned worker is terminated on deadline/cancellation/RSS excess, then killed if necessary. A separate cleanup grace is at most one second plus OS scheduling lag. **RSS polling can overshoot between samples; it is not a kernel hard memory cap.** Monitoring failure refuses execution. The total deadline includes preflight, reference calculation, imports, circuit compilation, sampling and original validation; serialization/reporting and cleanup overhead are reported. These software guards are not hard real-time guarantees. Peak RSS is an observed sampled maximum, separate from analytical/modeled memory.

The [1B operator certificate](evidence/checkpoint1b/operator-basis.json) checks all 512 Qiskit basis expectations against the unexpanded 1A reference (absolute tolerance 1e-10, relative 1e-12; observed error zero). Tests also cover Pauli string order, sign, identity offset and non-palindromic readouts under permuted measurement wiring and physical layout.

[Statevector output](evidence/checkpoint1b/qaoa-statevector.json), [Aer output](evidence/checkpoint1b/qaoa-aer.json) and [lifecycle probes](evidence/checkpoint1b/worker-limits.json) are real local runs. The statevector experiment's full 16-evaluation repeat reproduced raw counts, parameter path and decoded results exactly on this environment. This is reproducibility evidence, not a statistical performance benchmark or quantum advantage.

## Optional Mapper cross-check

Mapper 0.1.0 is isolated in `.venv-mapper`, with a separate [hashed lock](requirements/mapper-macos-arm64-py312.lock) and [exact snapshot](requirements/mapper-snapshot.txt). Install the quantum lock's build tools first, then the Mapper lock with `--no-build-isolation --require-hashes`; Docplex 2.32.264 is source-only in the resolved set. The isolated check does not run commercial solvers or cloud services:

```sh
.venv-mapper/bin/python scripts/check_mapper.py
```

The [saved cross-check](evidence/checkpoint1b/mapper-crosscheck.json) compares the exact reduced variables, explicit penalty 16, canonical coefficients/offset, all 512 energies/Ising expectations and six feasible assignments. Direct core execution remains the QAOA path. No general converter correctness or broader compatibility is claimed.

## Targeted 1C correction review

The [correction report](docs/IMPLEMENTATION_REPORT.md) and [executed commands](evidence/checkpoint1c-corrections/commands.md) record the fixture-reference patch, bounded startup investigation and fresh acceptance runs. The 20-second tiny OR-Tools audit did not reproduce the historical long delays; its cause remains unproven, and no timeout was raised to hide it. Worker metadata now separates process-start call, first event/bootstrap observation, native imports, model/solver dispatch, native solver and cleanup; these nested intervals must not be summed as disjoint stages.

Create a **sanitized source-only** review package from committed HEAD using:

```sh
.venv-api/bin/python scripts/create_review_archive.py --output review-snapshots/checkpoint1c-corrections.zip
```

The new `.zip.manifest.json` sidecar covers the exact ZIP member set, including required `.gitignore`, `.github/workflows/checks.yml`, `.githooks/pre-commit` and the embedded manifest. Verify the archive SHA after transfer; hidden files should be inspected with a ZIP listing, not a shell `*` glob. Git internals/history bundles, virtual environments, installed modules, caches and untracked files are excluded. Old evidence is preserved verbatim and old manifests describe their own checkpoints. The three reported missing files exist in this repository and in the prior ZIP retained here; the reviewer copy's omission cannot be explained from available evidence.

For new test evidence, set `QWS_EVIDENCE_DIR` to an absolute correction-evidence path before frontend tests; the default continues to target the original 1C directory for compatibility. No license is chosen. Stop for correction review and separate Phase 2 approval; no later phase is authorized.
