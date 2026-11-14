# Admissions preview command record — 7 November 2026

Commands ran in the isolated preview worktree. Paths below use project-relative
runtime names; `.venv-api` initially referred to the original pinned interpreter
and was then a local symlink to that same environment. `.tools` similarly selected
the unchanged pinned Node/browser runtime. These symlinks are excluded from exports.
No production source or lock was changed, no quantum experiment ran, no push occurred.

## Safeguard / isolation

Read AGENTS, full brief, README, full historical implementation report, 3B-M and
protected gate reports, architecture/decisions and phase plan. Recorded original
`git status --porcelain=v1`, branch, HEAD, staged diff and untracked paths before
edits. Saved file/index SHA-256, binary staged/unstaged patches and a private backup
of unfinished 3B-S paths. Then, through protected Git approval:

```sh
git worktree add -b codex/admissions-preview /private/tmp/ajita-admissions-preview 7cec5f41c8b28f0525c940a3e87d6aaa497811d0
```

That is a new worktree/branch, not a reset, stash, switch of the dirty checkout,
Finder ZIP import or history rewrite. Copied only the already executed historical
gate report/evidence; did not copy or stage the unfinished B1 runner/script/tests.

## Installs and checks

```sh
npm ci --prefix frontend --offline --no-audit --no-fund --cache /private/tmp/ajita-3bs-repair-npm-cache
```

First install failed ENOSPC; log retained. Preserved its partial tree outside the
worktree, reused pinned modules temporarily for the first checks. After free space
recovered without deleting user files, a fresh locked offline install succeeded,
136 packages. Both logs are retained; no lock/version or install-script permission
changed. Python used existing pinned packages; not a fresh Python install.

```sh
PYTHONPATH=src:tests .venv-api/bin/python -m pytest -p mapping_only_policy tests/test_classical.py tests/test_qubo.py tests/test_cli.py tests/test_timetable.py tests/api tests/test_review_archive.py -q --mapping-policy-evidence=evidence/admissions-preview/classical-policy.json --junitxml=evidence/admissions-preview/classical.xml
QWS_EVIDENCE_DIR="$PWD/evidence/admissions-preview" npm --prefix frontend test
npm --prefix frontend run build
PYTHONPATH=src QWS_PYTHON=.venv-api/bin/python sh .githooks/pre-commit
```

After the fresh npm install, reran the same Vitest/build/hook with distinct
`*-fresh-final.log` filenames and the Vitest evidence directory
`evidence/admissions-preview/fresh-frontend/`. Latest results: 12 component tests,
build and full normal hook passed. No `--no-verify` or check disabling.

Drafted privacy exporter and its four unit cases, ran Ruff format/check, then:

```sh
PYTHONPATH=src .venv-api/bin/python -m pytest tests/test_admissions_archive.py tests/test_review_archive.py -q --junitxml=evidence/admissions-preview/archive-tests.xml
```

Oversized input exposed slow regex scanning; retained partial log, interrupted and
then terminated only that owned test when SIGINT did not stop it. No initial XML
was produced (copy attempt of that nonexistent XML failed). Added early size refusal
and bounded email matching; Ruff passed and the focused rerun used new files:

```sh
PYTHONPATH=src .venv-api/bin/python -m pytest tests/test_admissions_archive.py tests/test_review_archive.py -q --junitxml=evidence/admissions-preview/archive-tests-final.xml
```

Seven passed: four new and three existing. These three existing are already among
the 650 classical cases; do not count repeated executions as additional coverage.

## Actual demos / browser

```sh
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli solve --instance examples/tsp/four_city.json --solver exact_tsp --output evidence/admissions-preview/tsp-exact.json
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli solve --instance examples/tsp/four_city.json --solver ortools_tsp --scale 1000 --timeout-s 1 --output evidence/admissions-preview/tsp-ortools.json
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver cp_sat --output evidence/admissions-preview/timetable-cp-sat.json
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver enumeration --output evidence/admissions-preview/timetable-enumeration.json
QWS_ENABLE_LOCAL_QUANTUM=0 PYTHONPATH=src .venv-api/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1
npm --prefix frontend run dev
```

Owned loopback servers were verified through approved local HTTP access after a
sandbox PermissionError. Health said quantum disabled/unavailable; UI HTML arrived.
Actual CLI objectives were 4/4 and 1/1. The first browser filter accidentally included
a mixed quantum/fixture flow: the server refused it with 400, 7 passed/1 failed,
no sampler execution. Preserve initial XML/log. Fixed only preview configuration to
exclude all four quantum-bearing flows; from frontend/ with pinned PATH/browser:

```sh
QWS_EVIDENCE_DIR="$PWD/../evidence/admissions-preview/browser-classical-final" PLAYWRIGHT_BROWSERS_PATH="$PWD/../.tools/playwright" npm run e2e -- --config playwright.preview.config.ts
```

Seven existing real classical Chromium flows passed; no intercepted/mock successes.
Original tests/config are unchanged. Reused two original screenshot bytes for the
README and visually inspected them; no video generated. Owned server cleanup was
checked (the earlier managed session ID had expired; no new server was started).
No absolute orphan-cleanup guarantee is claimed.

## Packaging and provenance

Read official MIT/Apache license texts for a recommendation only. No LICENSE added.
Preserved raw results; created privacy/ANSI projections with source hashes. The
first privacy scan caught two synthetic adversarial XML parameter IDs; only the
portable view relabeled them. Targeted scan then passed; raw XML is unchanged.

Standard-library/Git audits: document links/fences/SOP word count, unchanged
production/math/API/frontend-source/locks, original checkout/index preservation,
full relative inventory, screenshot hashes, XML totals and source hashes. Package
commands after committing the tested candidate:

```sh
.venv-api/bin/python scripts/create_admissions_archive.py --output <local-bundle-directory>/ajita-admissions-preview-source.zip
.venv-api/bin/python scripts/create_review_archive.py --output <local-bundle-directory>/ajita-research-<commit>.zip
```

First is curated/privacy-scanned source; second is a **private research bundle**,
not an online-upload candidate. Both verify actual members/hashes/CRC and required
hidden files; source commit and whole-ZIP hashes are emitted in sidecars. No Git
internals, installed modules, build caches, draft runner or Finder ZIP is imported.

Final exporter hardening explicitly denies all four unfinished B1 draft paths,
even if a later caller accidentally adds them to its input entries. The curated
export test was extended to exercise that refusal. The same focused seven-test
selection passed again with distinct `archive-publication-final.log/.xml`; portable
archive-test evidence now points to that final run. No production test was changed.
