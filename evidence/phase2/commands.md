# Phase 2 executed commands — 18 October 2026

Run from `/Users/pradumnkapil/proj/ajita`. No installation, dependency update, cloud request, remote push or publication occurred. Source/file-writing commands and read-only `cat`/`rg`/Git inspections were also used during development; this ledger records all test/build/evidence gates and their failures. Existing dependency locks are unchanged. `python3` is the system 3.14 interpreter and was used only for text editing; application/test commands below use the pinned 3.12 environments.

## Binding baseline and official API references

Read `PROJECT_BRIEF.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PHASE_PLAN.md` in full before implementation. Baseline Git status: `?? ARCHIVE_MANIFEST.json`; its contents were not read or changed. Accepted baseline: `2f66cdf`. The untracked root manifest is excluded from committed-HEAD source packaging.

Official current CP-SAT status/API and scheduling pages reviewed:
- https://developers.google.com/optimization/cp/cp_solver
- https://developers.google.com/optimization/scheduling/employee_scheduling

Installed OR-Tools is 9.15.6755. Native snake-case `new_bool_var`, `add_exactly_one`, `add_at_most_one`, `minimize`, `solve`, `status_name`, `value`, `best_objective_bound` and `wall_time` execute in real tests. No archived Optimization dependency or B1 converter was added.

## Targeted development runs

```sh
.venv-api/bin/ruff check --fix src/quantum_workload_studio/models/timetable.py src/quantum_workload_studio/classical/timetable.py src/quantum_workload_studio/qubo/timetable.py
.venv-api/bin/ruff format src/quantum_workload_studio/models/timetable.py src/quantum_workload_studio/classical/timetable.py src/quantum_workload_studio/qubo/timetable.py
.venv-api/bin/python -m pytest tests/test_timetable.py -q --junitxml=evidence/phase2/mathematical-core.xml
.venv-api/bin/python -m pytest tests/api/test_timetable.py -q --junitxml=evidence/phase2/api-initial.xml
.venv-api/bin/python -m pytest tests/api/test_timetable.py -q --junitxml=evidence/phase2/api.xml
.venv-api/bin/python -m pytest tests/test_timetable.py tests/api/test_timetable.py -q --junitxml=evidence/phase2/backend-targeted.xml
.venv-api/bin/python -m pytest tests/test_timetable.py tests/api/test_timetable_service.py -q --junitxml=evidence/phase2/backend-targeted.xml
.venv-api/bin/python -m pytest tests/test_timetable.py tests/api/test_timetable_service.py -q --junitxml=evidence/phase2/backend-final.xml
```

Chronological outcomes:
1. Initial mathematical test collection: **one syntax error** in the new parametrization decorator; corrected. Preserved as `mathematical-core-initial-collection-failure.{log,xml}`. Initial Ruff also reported that parse error/one-line blocks; formatter succeeded after syntax correction. Next core run: **37 passed**.
2. Initial API run: **9 passed, 2 failed** because the new lifecycle test imported a nonexistent test helper `default_instance`. Replaced that test-only import with the existing four-city JSON fixture. Preserved `api-initial.{log,xml}`; next API run **11 passed** in `api.{log,xml}`.
3. Combined collection: **one import-file-mismatch collection error**, because both new test modules were named `test_timetable.py`. Renamed only the new API module to `test_timetable_service.py`; no global pytest behavior changed. Failure retained as `backend-targeted-collection-failure.{log,xml}`; next combined run **50 passed**.
4. Added ties, zero-variable capacity proof, real native UNKNOWN, strict schema/encoding version regressions and a real native FEASIBLE check (test-controlled CP-SAT stop-after-first-solution/presolve settings). Targeted final: **61 passed**, one existing Starlette warning. These are unit controls, not production option settings or benchmark runs.

## Mathematical evidence and preservation

```sh
.venv-api/bin/ruff format scripts/evidence_timetable.py scripts/audit_phase2_preservation.py
.venv-api/bin/ruff check scripts/evidence_timetable.py scripts/audit_phase2_preservation.py
.venv-api/bin/python scripts/evidence_timetable.py > evidence/phase2/mathematical-evidence.log
.venv-api/bin/python scripts/audit_phase2_preservation.py > evidence/phase2/environment-and-preservation.json
.venv-api/bin/python -m pip check > evidence/phase2/pip-check-classical.log 2>&1
.venv-api-quantum/bin/python -m pip check > evidence/phase2/pip-check-quantum.log 2>&1
.venv-api/bin/python -m pip list --format=json > evidence/phase2/packages-classical.json
.venv-api-quantum/bin/python -m pip list --format=json > evidence/phase2/packages-quantum.json
sw_vers
uname -mrs
.tools/node-v24.22.0-darwin-arm64/bin/node --version
.tools/node-v24.22.0-darwin-arm64/bin/npm --version
```

Evidence script: four original-domain oracle/CP-SAT pairs agree, with all 16/4/1/16 binary assignments checked; zero energy discrepancies at absolute tolerance 1e-12 on these fixtures. Preservation audit: **126/126 old tracked evidence/requirements files identical** against `2f66cdf`. Both `pip check` calls: no broken requirements; pip warns its global cache is unwritable and disables it (no installation attempted). Versions/package lists are authentic outputs.

Tooling failures during environment reporting: an initial inline audit was mistakenly invoked with system `python3` 3.14, which lacks OR-Tools metadata; it failed with `PackageNotFoundError: ortools`, after completing its read-only preservation loop. A trailing accidental `.tail_not_a_command` shell token returned command-not-found (exit 127). Neither produced a valid environment report or changed source. Replaced the inline audit with the reviewed script above, invoked under `.venv-api/bin/python`; the committed JSON is from that successful execution. No fabricated metadata substitutes for the failed invocation.

## Final acceptance commands

```sh
export PATH="$PWD/.tools/node-v24.22.0-darwin-arm64/bin:$PATH"
.venv-api/bin/python scripts/export_openapi.py
npm --prefix frontend run types
npm --prefix frontend run format
sh scripts/check_quality.sh > evidence/phase2/quality-final.log 2>&1
npm --prefix frontend run build > evidence/phase2/frontend-build-final.log 2>&1
QWS_EVIDENCE_DIR=../evidence/phase2 npm --prefix frontend test > evidence/phase2/vitest-final.log 2>&1
.venv-api-quantum/bin/python -m pytest -q --junitxml=evidence/phase2/full-macos-quantum.xml > evidence/phase2/full-macos-quantum.log 2>&1
.venv-api/bin/python -m pytest tests/test_classical.py tests/test_qubo.py tests/test_cli.py tests/test_timetable.py tests/api -q --junitxml=evidence/phase2/classical-macos.xml > evidence/phase2/classical-macos.log 2>&1
QWS_EVIDENCE_DIR=../evidence/phase2 PLAYWRIGHT_BROWSERS_PATH="$PWD/.tools/playwright" npm --prefix frontend run e2e > evidence/phase2/playwright-final.log 2>&1
```

Actual final outcomes: **1,186 Python passed** with zero failures/errors/skips in optional environment; classical selection **647 passed, one intentional Qiskit-only skip**; four existing warnings in each (three SWIG, one Starlette/HTTPX deprecation). Build passed; **12 Vitest tests passed**; **11 real Chromium tests passed**; quality/OpenAPI/TypeScript drift checks passed. No frontend test intercepts a production success response in E2E. Vitest has explicitly labeled isolated response fixtures only. Browser screenshots were visually inspected for grid, scope/timing wording and layout. Earlier successful full suite (**1,175**) and classical selection (**636 + one skip**) preceded the 11 added version/status regressions; their logs/XML are retained with `-intermediate` suffix. Final suite was repeated after correcting null import timing for enumeration; authoritative files use the unsuffixed names.

Initial E2E invocation under sandbox failed to bind loopback port 8000 (`operation not permitted`), preserved in `playwright-initial.log`. The authorized run outside that restriction passed all 11 flows in `playwright.log`; final repeated runs also passed, in `playwright-final.log`. Earlier builds/format/Vitest logs remain in this directory. The first quality check detected unformatted new `Timetable.test.tsx`; Prettier corrected it and the final quality gate passes. No production deadline was increased to hide a failure. Final XML, response JSON and screenshots describe the latest execution; earlier successful test logs are historical runs, not claimed to share identical timings with the latest JSON.

## Git and sanitized review package

Tested commits: `33291e4` mathematical core, `22e4685` bounded API/CLI, `3216e60` strict versions/native status tests, `f9e22a2` UI. Later timing/provenance/documentation commits are listed by final Git log, not invented in advance. Pre-commit hook ran the actual quality gate on each commit. Git commits used sandbox escalation because `.git` is protected; no remote command was used.

```sh
.venv-api/bin/python scripts/create_review_archive.py --output review-snapshots/phase2-source.zip
# Builder verifies exact members/digests, required hidden files, whole ZIP hash and CRC.
git log -8 --oneline
git status --short
```

The ZIP is built only after the report/evidence source commit. Its embedded manifest hashes payloads; the external `.zip.manifest.json` additionally hashes the embedded manifest and exactly every actual ZIP member. Its SHA-256 sidecar records the whole ZIP hash. No Git internals, untracked root manifest, environments/modules/caches, `.tools`, review archives, credentials or unrelated files are included. Source-only snapshot contains all committed historical evidence unchanged. No claim that targeted secret-marker checks provide a universal secret audit.

## Standalone final CLI evidence (also executed)

```sh
.venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver cp_sat --timeout-s 20 --output evidence/phase2/cli-cp-sat.json
.venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver enumeration --timeout-s 20 --output evidence/phase2/cli-enumeration.json
.venv-api/bin/python -m quantum_workload_studio.cli timetable compile --instance examples/timetable/tiny.json --output evidence/phase2/cli-qubo.json
.venv-api/bin/python -m quantum_workload_studio.cli timetable inspect --instance examples/timetable/tiny.json --qubo evidence/phase2/cli-qubo.json --bits 1001 --output evidence/phase2/cli-inspection.json
```

All four returned exit 0. Both real classical workers exited cleanly; both objective values are 1. The inspection reports original objective 1, feasible, QUBO energy 1. `acceptance-summary.json` was mechanically generated from final JUnit XML (`xml.etree.ElementTree`, summing actual tests/failures/errors/skipped on suites); no additional tests were invented by that summary. `afe3457` records the tested oracle timing/label correction and preservation audit. Final evidence/report commit follows that source milestone. Final Git log/status and ZIP hash are returned directly after packaging, avoiding circular source-commit hashes.
