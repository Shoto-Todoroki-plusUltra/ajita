# Quantum Workload Studio

Checkpoints **1A and 1B**: a classical TSP oracle, OR-Tools baseline, independently checked explicit QUBO and optional bounded local QAOA research experiment. No practical quantum speedup demonstrated; novelty unverified. Local quantum simulation executes classically. No cloud integration, API or frontend is implemented; 1C remains unauthorized.

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

Tests parameterize all 512 assignments independently, check the hand-tabulated routes and lower-bound proof, reject corrupt/malformed inputs/exports and exercise CLI behavior. [IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) records actual results and commands. The user reported external review of the 1A source/evidence; that reviewer lacked OR-Tools, so full Mac execution evidence remains separate. 1B human review is pending. Checkpoint 1C and later phases require explicit approval.

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
