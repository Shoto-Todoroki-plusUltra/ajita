# Quantum Workload Studio

Checkpoint **1A only**: a small classical TSP oracle, OR-Tools baseline and independently checked explicit QUBO mathematical core. No practical quantum speedup demonstrated; novelty unverified. No quantum optimizer, Qiskit/Mapper dependency, cloud integration, API or frontend is implemented.

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

Tests parameterize all 512 assignments independently, check the hand-tabulated routes and lower-bound proof, reject corrupt/malformed inputs/exports and exercise CLI behavior. [IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) records actual results and commands. User-directed design and Codex implementation are distinct; independent human code review is pending. Checkpoints 1B/1C and all later phases require explicit approval.
