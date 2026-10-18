# Executed targeted 1C corrections — 18 October 2026

Repository: `/Users/pradumnkapil/proj/ajita`. No dependency installation/version change, remote push, publication, paid job, timetable, CVRP or research benchmark was performed. Existing 1A/1B and initial 1C evidence was left untouched; new outputs use this directory.

## Inspection and changes

Read full `PROJECT_BRIEF.md`, `AGENTS.md`, relevant current UI/API/worker/test/quality sources and existing architecture/report/README. Ran `git status --short`, `git diff --check`, `git diff --stat`, `git log`, `rg`/`sed` reads and `ls -la .gitignore .github/workflows/checks.yml .githooks/pre-commit`. Optional `.gitattributes` read failed because it does not exist; none was manufactured. Python/zipfile and `git ls-files` verified the three required files are tracked and match their members in the previous local ZIP. The provenance of the reviewer's different copy is unknown; see `archive-input-audit.json`.

Edits used `apply_patch` and focused Python text updates. Two attempted patches failed on formatted test context before applying; fresh reads and a smaller patch corrected this. No application test was substituted by those tool errors. Ruff initially fixed import ordering in new instrumentation/scripts/tests. No required test failed in this correction run. Intentionally rejected inputs, guard timeouts and no-feasible outcomes remain test cases, not hidden successes.

## Sequential reliability audit (run before other test workloads)

```sh
.venv-api/bin/ruff check --fix src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/audit_cold_start.py
.venv-api/bin/ruff format src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/audit_cold_start.py
.venv-api/bin/python scripts/audit_cold_start.py --output evidence/checkpoint1c-corrections
QWS_AUDIT_EVIDENCE="$PWD/evidence/checkpoint1c-corrections/pytest-isolated" .venv-api/bin/python -m pytest tests/api/test_startup_timings.py -q --junitxml=evidence/checkpoint1c-corrections/pytest-isolated.xml
```

Approved loopback access was used. The driver starts three independent API interpreters with measured Uvicorn/API imports, each with two requests and a new spawned worker per request; then three standalone real workers. API/native solver deadline stays **20 seconds**; startup guard 10 seconds, audit guard 240 seconds, HTTP guard 23 seconds, server cleanup terminate/wait/kill guarded. All six HTTP responses were 200; all standalone workers completed; three isolated pytest cases passed. The first observation is not a first-ever machine import or proof of flushed disk/OS caches. Raw measurements and partial events are retained even on failure. There was no failure to discard in this audit, and no demonstrated root cause to fix.

## Acceptance checks

Frontend commands ran from `frontend/` with:

```sh
PATH="$PWD/../.tools/node-v24.22.0-darwin-arm64/bin:$PATH"
export QWS_EVIDENCE_DIR="$PWD/../evidence/checkpoint1c-corrections"
npm run format
npm test
npm run build > ../evidence/checkpoint1c-corrections/frontend-build.log 2>&1
PLAYWRIGHT_BROWSERS_PATH="$PWD/../.tools/playwright" npm run e2e
```

Vitest **9 passed**. Real Chromium **7 passed**, including a real solve/edit/re-solve sequence for same-ID changed matrix, coordinates and five cities, plus all earlier classical/local-quantum/error/timeout/cancellation flows. No route interception/mock success. A follow-up source change removed the stale sketch on edited input; Vitest/build/real browser suites were rerun successfully. Final Vitest rerun also checks the new backend-time label and latency qualifier. XML, response JSON and actual screenshots are in this directory. Test configs accept `QWS_EVIDENCE_DIR` so original evidence is not overwritten.

```sh
.venv-api/bin/ruff check --fix scripts/create_review_archive.py tests/test_review_archive.py
.venv-api/bin/ruff format scripts/create_review_archive.py tests/test_review_archive.py
.venv-api/bin/python -m pytest tests/test_review_archive.py -q --junitxml=evidence/checkpoint1c-corrections/archive-tests.xml
QWS_AUDIT_EVIDENCE="$PWD/evidence/checkpoint1c-corrections/pytest-full" .venv-api-quantum/bin/python -m pytest tests -q --junitxml=evidence/checkpoint1c-corrections/python-full.xml
.venv-api/bin/python -m pytest tests/api tests/test_classical.py tests/test_qubo.py tests/test_cli.py tests/test_review_archive.py -q --junitxml=evidence/checkpoint1c-corrections/python-classical.xml
PATH="$PWD/.tools/node-v24.22.0-darwin-arm64/bin:$PATH" sh scripts/check_quality.sh
.venv-api/bin/python -m pip check
.venv-api-quantum/bin/python -m pip check
sw_vers
```

Archive tests **3 passed**: required dotfiles, forbidden contents, exact member sets and tampering. Initial optional full run **1,122 passed** before adding those archive tests; final full run **1,125 passed**. Classical selection **589 passed / one intentional Qiskit-only skip**. Three original SWIG warnings and Starlette/HTTPX deprecation remain; no errors/failures. The full-suite timing probes are saved separately from the isolated ones. Frontend/build/test scheduling and ordinary desktop activity are not claimed to be eliminated; this is not an idle-system benchmark. Both pip checks passed. Actual Mac: 26.5.2, build 25F84, arm64, CPython 3.12.13; Node/Chromium pins unchanged.

Quality hook checks lint/format and unchanged generated OpenAPI/TypeScript contracts. Python snippets reconcile XML counts, derive reliability ranges from raw data, check source/lock/artifact fingerprints and confirm no changes to historical evidence/test/lock paths against `4b93eed`. `git diff --cached --check` ran before each commit; the hook ran on tested commits. Source milestone: `60b4fb6`.

## Sanitized source packaging

After the final documentation/evidence commit:

```sh
.venv-api/bin/python scripts/create_review_archive.py --output review-snapshots/checkpoint1c-corrections.zip
```

The source list/data comes from **committed HEAD only**. Required hidden files must be present; no glob omits dotfiles. Forbidden paths, installed environments/modules, caches, archives/bundles, private-key markers and credential-bearing URLs are refused. Targeted checks are not advertised as an exhaustive secret-detection guarantee. No Git directory or history bundle is included. The embedded manifest hashes every payload file; the external `.zip.manifest.json` is built from actual ZIP members and hashes every member **including the embedded manifest**, with whole-ZIP SHA-256. ZIP CRC, exact member-set equality and each hash are verified. This external manifest is authoritative for this new archive; earlier checkpoint manifests remain historical evidence.

The final commit and SHA are returned with the package. Review artifacts remain local under ignored `review-snapshots`; no publication is implied. Remote CI, other operating systems, Intel macOS, Safari/Firefox and Python 3.11 were not executed. The unexplained historical 20–30-second delay risk remains for review, without a speculative fix or timeout increase.
