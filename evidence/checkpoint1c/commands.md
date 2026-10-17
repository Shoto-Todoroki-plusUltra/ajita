# Executed commands — Checkpoint 1C, 16 October 2026

Working directory: `/Users/pradumnkapil/proj/ajita`, native macOS arm64. Commands below group repeated invocations; failures are retained in `development-failures.json`, the report and the initial failed XML. Source edits used `apply_patch` and focused Python text updates. This is an execution record, not a claim that unexecuted CI ran.

## Inspection and publisher references

`cat PROJECT_BRIEF.md` (full), `cat AGENTS.md docs/PHASE_PLAN.md`, `cat`/focused `sed` of ARCHITECTURE, DECISIONS, PRIOR_ART, models, classical/quantum runners, CLI, tests, pyproject and README; `git status --short`, `git diff --check`, `git diff --cached --check`, `git diff --stat`, `git log`; `rg` for schema caps/imports/type-generator exports. Initial `node --version` = 25.9.0, `npm --version` = 11.12.1, `command -v node` = `/opt/homebrew/bin/node`.

Official FastAPI, Vite, Node release/archive, Playwright web-server, OpenAPI TypeScript, setup-node and GitHub runner documentation were read with web tools; URLs are in the report. Registry queries using the local Node LTS: `npm view vite version`, `npm view react version`, `npm view vitest version`, `npm view @playwright/test version`. Published package resolution was then pinned, not assumed compatible.

## Python environments and locks

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api
.venv-api/bin/python -m pip install --no-index --find-links /private/tmp/qws-1a-wheels --require-hashes -r requirements/macos-arm64-py312.lock
.venv-api/bin/python -m pip install fastapi uvicorn httpx psutil ruff
.venv-api/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-api/bin/python -m pip freeze --all --exclude quantum-workload-studio > requirements/api-macos-arm64-py312-snapshot.txt
.venv-api/bin/python -m pip download --only-binary=:all: -r requirements/api-macos-arm64-py312-snapshot.txt -d /private/tmp/qws-api-wheels
.venv-api/bin/python -m piptools compile --no-index --find-links /private/tmp/qws-api-wheels --constraint requirements/api-macos-arm64-py312-snapshot.txt --generate-hashes --allow-unsafe --no-emit-index-url --no-emit-find-links --output-file requirements/api-macos-arm64-py312.lock requirements/api.in
```

The last invocation initially failed on the default home-cache permission. Approved retry added `--cache-dir /private/tmp/qws-piptools-cache`; it succeeded offline. The quantum lock was compiled with the same flags plus `--strip-extras`, additional wheel locations `/private/tmp/qws-1b-wheels` and `/private/tmp/qws-1a-wheels`, output `requirements/api-quantum-macos-arm64-py312.lock`, input `requirements/api-quantum.in`.

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api-quantum
.venv-api-quantum/bin/python -m pip install --no-index --find-links /private/tmp/qws-1b-wheels --find-links /private/tmp/qws-1a-wheels --require-hashes -r requirements/quantum-macos-arm64-py312.lock
.venv-api-quantum/bin/python -m pip install --no-index --find-links /private/tmp/qws-api-wheels -r requirements/api-macos-arm64-py312-snapshot.txt
.venv-api-quantum/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-api-quantum/bin/python -m pip install --force-reinstall --no-index --find-links /private/tmp/qws-api-wheels --find-links /private/tmp/qws-1b-wheels --find-links /private/tmp/qws-1a-wheels --require-hashes -r requirements/api-quantum-macos-arm64-py312.lock > evidence/checkpoint1c/quantum-hash-reinstall.log 2>&1
.venv-api-quantum/bin/python -m pip check
/opt/homebrew/bin/python3.12 -m venv .venv-api-clean
.venv-api-clean/bin/python -m pip install --no-index --find-links /private/tmp/qws-api-wheels --require-hashes -r requirements/api-macos-arm64-py312.lock > evidence/checkpoint1c/fresh-classical-install.log 2>&1
.venv-api-clean/bin/python -m pip install --no-deps --no-build-isolation -e . >> evidence/checkpoint1c/fresh-classical-install.log 2>&1
.venv-api-clean/bin/python -m pip check
```

All installs/imports/pip checks above actually ran. Read-only Python snippets saved interpreter/platform/package metadata, verified classical API imports did not load Qiskit and verified Qiskit was absent from `.venv-api-clean`. Original `.venv`/`.venv-quantum` and historical locks were not upgraded.

## Node/frontend

```sh
curl -fL --max-time 60 https://nodejs.org/dist/v24.22.0/SHASUMS256.txt -o /private/tmp/qws-node-shasums.txt
curl -fL --max-time 120 https://nodejs.org/dist/v24.22.0/node-v24.22.0-darwin-arm64.tar.gz -o /private/tmp/qws-node.tar.gz
```

A Python snippet compared the archive SHA-256 to the named official checksum before `tarfile.extractall('.tools', filter='data')`; saved `node-toolchain.txt`. No global installation. A later poll of the already-completed download process returned a stale-session error; the checksum and extraction verified the actual downloaded file.

Frontend commands ran from `frontend/` with `PATH="$PWD/../.tools/node-v24.22.0-darwin-arm64/bin:$PATH"`:

```sh
npm install --cache /private/tmp/qws-npm-cache --save-exact react@19.3.1 react-dom@19.3.1
npm install --cache /private/tmp/qws-npm-cache --save-dev --save-exact vite@8.3.4 vitest@5.0.5 @vitejs/plugin-react typescript @types/react @types/react-dom @types/node jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @playwright/test openapi-typescript prettier
npm install --cache /private/tmp/qws-npm-cache --save-dev --save-exact typescript@5.9.3
npm run types
npm run format
npm run build
npm test
npm run types:check
npm ci --offline --cache /private/tmp/qws-npm-cache > ../evidence/checkpoint1c/fresh-npm-ci.log 2>&1
npm run build > ../evidence/checkpoint1c/frontend-build.log 2>&1
npm ls --depth=0
PLAYWRIGHT_BROWSERS_PATH="$PWD/../.tools/playwright" npx playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/../.tools/playwright" npm run e2e
```

Type generation initially failed under resolved TypeScript 7.0.2; the exact 5.9.3 retry satisfies the generator peer range. Two builds failed on missing required generated request fields; supplying actual fields fixed them. No unsafe cast was added to bypass those errors. The successful fresh `npm ci`, Vitest, build and type check ran again. The first sandboxed E2E failed binding loopback port 8000; approved local-server/browser retry passed five tests initially and six after adding genuine cancellation/concurrency coverage. The final six-test run also covers the final 8,192-shot HTTP trace cap configuration. All final E2E responses are real; unit fixtures are explicitly labeled in their test source.

## Python tests and quality checks

```sh
.venv-api/bin/python -m pytest tests/api -q --junitxml=evidence/checkpoint1c/api-development.xml
.venv-api-quantum/bin/python -m pytest tests/api -q --junitxml=evidence/checkpoint1c/api-quantum-development.xml
.venv-api/bin/python -m pytest tests/test_classical.py tests/test_qubo.py tests/test_cli.py -q --junitxml=evidence/checkpoint1c/original-1a-tests.xml
.venv-quantum/bin/python -m pytest tests/test_classical.py tests/test_qubo.py tests/test_cli.py tests/quantum -q --junitxml=evidence/checkpoint1c/reproduced-1b-1103-tests.xml
.venv-api-clean/bin/python -m pytest tests/api tests/test_classical.py tests/test_qubo.py tests/test_cli.py -q --junitxml=evidence/checkpoint1c/fresh-classical-tests.xml
.venv-api-quantum/bin/python -m pytest tests -q --junitxml=evidence/checkpoint1c/full-quantum-api-tests.xml
.venv-api/bin/python scripts/export_openapi.py
.venv-api/bin/python scripts/export_openapi.py --check
.venv-api/bin/ruff check --fix src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py src/quantum_workload_studio/cli.py
.venv-api/bin/ruff format src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py
PATH="$PWD/.tools/node-v24.22.0-darwin-arm64/bin:$PATH" sh scripts/check_quality.sh
chmod +x scripts/check_quality.sh .githooks/pre-commit
git config core.hooksPath .githooks
```

Initial API run: 11 passed/1 failed/1 skipped at five-second OR-Tools timeout. Its corrected 30-second development run passed 12/one skip; optional development run passed 13. A fresh classical acceptance initially failed once at 30 seconds; copied unchanged to `fresh-classical-initial-failure.xml` before rerun. The latest fresh suite passes **583 with one intentional quantum-only skip**; full optional suite **1,119 with no skips/failures**. The independent original **1,103** suite and **568** 1A files pass unchanged. `api-*-development.xml` are intermediate snapshots, not the final test count.

## Manual browser, diagnostics and packaging

Approved loopback manual servers: `QWS_ENABLE_LOCAL_QUANTUM=1 .venv-api-quantum/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1`, and (frontend directory, pinned Node PATH) `npm run dev`. Desktop browser controls opened `http://127.0.0.1:5173`, clicked actual OR-Tools/local-QAOA flows and inspected the accessibility result; the temporary tab was closed. Ctrl-C stopped both owned servers, confirmed by Uvicorn shutdown output. `manual-browser-review.md` preserves initial timeout and later successful results.

Diagnostic Python snippets ran a timeout-bounded fresh OR-Tools import and repeated real HTTPX API requests; saved import/request probe JSON. An approved `ps -axo pid,ppid,etime,stat,command` inspection was too broad/noisy and was not saved into artifacts. An attempt to sample only the owned worker found it already gone; a bounded request/sample probe then had a diagnostic integer-status-call error. Corrected probe recorded real requests. No stack sample exists, and no causal claim is made. Diagnostic errors are not solver results.

Read-only audit snippets check XML counts, original evidence/test/lock equality against `f6ee8e2`, local documentation links, source/package/lock fingerprints, raw shot reconciliation and owned worker/server cleanup. The final manifest records source/evidence hashes; inventory excludes `ajita.zip` and installed tools/modules. Git stages only explicit project paths. `git diff --cached --check` preceded each commit. API milestone `81cb6d0`; tested UI/guard/quality milestone `7fc59f6`. The hook actually passed during the UI commit. Final report/evidence milestone is identified by Git log, avoiding a self-referential hash.

The review ZIP is a `git archive` of the final commit, with a separate Git-history bundle and review metadata added for reconstructing historical checkpoint source hashes. SHA-256 and ZIP CRC are verified after creation. These ignored `review-snapshots` artifacts are local only; no push, registry publication, dependency license choice or cloud resource action was performed.
