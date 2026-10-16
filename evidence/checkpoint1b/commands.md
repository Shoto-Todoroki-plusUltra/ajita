# Checkpoint 1B command journal

Executed on the development arm64 Mac with CPython 3.12.13, 15 October 2026. Commands are run from the repository root. Registry downloads and protected Git mutations used sandbox escalation approval. No command contacted an IBM service or used credentials. Temporary distribution directories are not committed.

## Environment (succeeded)

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-quantum
.venv-quantum/bin/python -m pip install --no-index --find-links /private/tmp/qws-1a-wheels --require-hashes -r requirements/macos-arm64-py312.lock
.venv-quantum/bin/python -m pip install qiskit==2.5.2 qiskit-aer==0.17.2 scipy==1.18.0 'psutil>=7,<9'
.venv-quantum/bin/python -m pip freeze --all > /private/tmp/qws-1b-resolved.txt
.venv-quantum/bin/python -m pip download --only-binary=:all: --dest /private/tmp/qws-1b-wheels -r /private/tmp/qws-1b-resolved.txt
.venv-quantum/bin/pip-compile --no-index --find-links /private/tmp/qws-1b-wheels --no-emit-options --allow-unsafe --generate-hashes --strip-extras --cache-dir /private/tmp/qws-1b-lock --output-file requirements/quantum-macos-arm64-py312.lock requirements/quantum.in
.venv-quantum/bin/python -m pip install --no-index --find-links /private/tmp/qws-1b-wheels --require-hashes --force-reinstall -r requirements/quantum-macos-arm64-py312.lock
.venv-quantum/bin/python -m pip install --no-index --no-deps --no-build-isolation -e .
.venv-quantum/bin/python -m pip check
.venv-quantum/bin/python scripts/check_quantum_environment.py > evidence/checkpoint1b/environment-smoke.json
```

The installed psutil resolved to 7.2.2 and was then pinned in the quantum input. Base pins and classical lock were not changed. Reinstallation verifies the native wheel hashes. For a new machine, install from the committed hashed lock as documented in README; the temporary wheel cache is optional.

## Operator, lifecycle and experiments

```sh
.venv-quantum/bin/python scripts/record_operator.py
.venv-quantum/bin/python -m pytest tests/quantum/test_operator.py -q --junitxml=evidence/checkpoint1b/operator-tests.xml
.venv-quantum/bin/python -m pytest tests/quantum/test_local.py -q -x --tb=short --junitxml=evidence/checkpoint1b/local-tests.xml
.venv-quantum/bin/python scripts/record_worker_limits.py
.venv-quantum/bin/python -m quantum_workload_studio.local_cli --instance examples/tsp/four_city.json --output evidence/checkpoint1b/qaoa-statevector.json --evaluations 16 --shots 256 --seed 1729 --timeout-s 60
.venv-quantum/bin/python -m quantum_workload_studio.local_cli --instance examples/tsp/four_city.json --output evidence/checkpoint1b/qaoa-statevector-repeat.json --evaluations 16 --shots 256 --seed 1729 --timeout-s 60
.venv-quantum/bin/python -m quantum_workload_studio.local_cli --instance examples/tsp/four_city.json --output evidence/checkpoint1b/qaoa-aer.json --backend aer --evaluations 16 --shots 256 --seed 1729 --timeout-s 60
```

Initial operator-test run: 512 setup errors/7 passes due to a wrong fixture path; corrected and rerun to 519 passes. No operator disagreement occurred. Local-test run before later additional tests: 8 passes. Later full suite below is authoritative. Experiments were rerun after adding watchdog-interval metadata; saved outputs correspond to the current source hashes. Comparisons of all recorded raw counts, parameters and decoded summaries between the two statevector files passed. The best feasible route comes only from measured samples; no oracle route is copied into candidate output.

## Optional Mapper, isolated and time-boxed

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-mapper
.venv-mapper/bin/python -m pip install --no-index --find-links /private/tmp/qws-1b-wheels --require-hashes -r requirements/quantum-macos-arm64-py312.lock
.venv-mapper/bin/python -m pip install --dry-run --only-binary=:all: qiskit-addon-opt-mapper==0.1.0
```

The wheel-only dry-run failed: no Docplex wheel available in the resolved index. One subprocess-bounded retry (180 seconds) ran the following command successfully in 23.66 seconds. Its exit status/elapsed time and raw log are saved in `mapper-install.json`/`mapper-install.log`.

```sh
.venv-mapper/bin/python -m pip install qiskit-addon-opt-mapper==0.1.0 qiskit==2.5.2 numpy==2.5.4 scipy==1.18.0 --timeout=15 --retries=1
.venv-mapper/bin/python -m pip install --no-index --no-deps --no-build-isolation -e .
.venv-mapper/bin/python scripts/check_mapper.py
.venv-mapper/bin/python -m pip freeze --all --exclude quantum-workload-studio > requirements/mapper-snapshot.txt
.venv-mapper/bin/python -m pip download --no-deps --dest /private/tmp/qws-mapper-dist -r requirements/mapper-snapshot.txt --timeout=15 --retries=1
.venv-mapper/bin/pip-compile --no-index --find-links /private/tmp/qws-mapper-dist --no-build-isolation --no-emit-options --allow-unsafe --generate-hashes --strip-extras --cache-dir /private/tmp/qws-mapper-lock --output-file requirements/mapper-macos-arm64-py312.lock requirements/mapper.in
.venv-mapper/bin/python -m pip install --no-index --find-links /private/tmp/qws-mapper-dist --no-build-isolation --require-hashes --dry-run --ignore-installed -r requirements/mapper-macos-arm64-py312.lock > evidence/checkpoint1b/mapper-lock-verification.log
.venv-mapper/bin/python -m pip check
```

Mapper computation is guarded at 30 seconds and completed in ~0.26 seconds. The optional cross-check uses explicit reduced variables and penalty 16, not the library's unreduced TSP application. Its environment includes CVXPY/Docplex and their dependencies; no commercial solver or provider is invoked. The direct-core environment remains separate.

## Final regression/verification

```sh
.venv/bin/python -m pytest tests/test_classical.py tests/test_qubo.py tests/test_cli.py -q --junitxml=evidence/checkpoint1b/1a-regressions.xml
.venv-quantum/bin/python -m pytest tests/quantum -q -x --tb=short --junitxml=evidence/checkpoint1b/quantum-tests.xml
.venv-quantum/bin/python -m pytest -q -x --tb=short --junitxml=evidence/checkpoint1b/full-quantum-environment-tests.xml
git diff --check
git diff --cached --check
git status --short
git log --oneline
```

Original suite: 568 passes, zero failures/errors/skips. Full current suite: 1,103 passes, zero failures/errors/skips, three original SWIG deprecation warnings. Intermediate quantum-only XML covers 532 tests before the last three error/CLI tests were added. A read-only Python audit compared every original baseline file with Git commit `e716ed7` (except explicitly updated README/report/optional pyproject metadata), verified source/lock/artifact hashes and test XML counts, and confirmed full repeated-experiment determinism. `ajita.zip` was already untracked at task start and was not inspected or committed.
