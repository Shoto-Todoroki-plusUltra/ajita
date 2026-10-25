# 3B-M command record

Run from `/Users/pradumnkapil/proj/ajita` on 25 October 2026. No installs,
sampler runs or benchmark batches. Shell redirection saves authentic output.

```sh
# Initial new-test run (failed test constant; retained, not passing evidence).
PYTHONPATH=tests .venv-api-quantum/bin/python -m pytest -p mapping_only_policy tests/quantum/test_research_mapping.py -q --mapping-policy-evidence=evidence/3bm/targeted-policy.json --junitxml=evidence/3bm/mapping-initial.xml > evidence/3bm/mapping-initial.log 2>&1

# Intermediate full permitted selection.
PYTHONPATH=tests .venv-api-quantum/bin/python -m pytest -p mapping_only_policy -q --mapping-policy-evidence=evidence/3bm/full-policy.json --junitxml=evidence/3bm/full-mapping-only.xml > evidence/3bm/full-mapping-only.log 2>&1

# Final permitted selection, after source fixes.
PYTHONPATH=tests .venv-api-quantum/bin/python -m pytest -p mapping_only_policy -q --mapping-policy-evidence=evidence/3bm/final-policy.json --junitxml=evidence/3bm/final-mapping-only.xml > evidence/3bm/final-mapping-only.log 2>&1

# Final classical-only environment regression.
PYTHONPATH=tests .venv-api/bin/python -m pytest -p mapping_only_policy tests/test_classical.py tests/test_qubo.py tests/test_cli.py tests/test_timetable.py tests/api tests/test_review_archive.py -q --mapping-policy-evidence=evidence/3bm/classical-policy.json --junitxml=evidence/3bm/classical.xml > evidence/3bm/classical.log 2>&1

# Fixed exhaustive math certificate; existing guarded worker, no sampler.
.venv-api-quantum/bin/python scripts/certify_research_mapping.py > evidence/3bm/certificate-command.log 2>&1
PATH="$PWD/.tools/node-v24.22.0-darwin-arm64/bin:$PATH" scripts/check_quality.sh > evidence/3bm/quality.log 2>&1
.venv-api-quantum/bin/python -m pip check > evidence/3bm/quantum-pip-check.log 2>&1

# Packaging, after report/evidence commit. Prints actual ZIP hash and verifies it.
.venv-api/bin/python scripts/create_review_archive.py --output review-snapshots/3bm-mapping-source.zip
```

Additional read-only inspection commands: `git status --short`, `git log`,
`git diff`, `git ls-tree`, `git show`, `sw_vers`, Python package metadata and Node
`--version`. Preservation audit compared SHA-256/bytes of baseline tracked files
with their current files; results in `preservation.json`. `environment.json`
records actual installed versions; certificate provenance records every source
hash, quantum lock hash and protocol hash. `inventory.json` is derived from Git
diff against the accepted Phase 3A baseline plus new evidence/report paths.

Safety policy is explicitly loaded only for these pytest invocations. Do not
remove it and run the entire suite under the mapping-only authorization: six
existing tests execute forbidden samplers/workers. Deselections are not passes.

Initial formatting/lint repair commands used `python -m ruff check --fix` and
`python -m ruff format` on the new mapping modules/tests and `ruff check --fix`
on the touched legacy import lists; final hook output is retained. Git commits
also run that same quality hook. No public API schema or frontend output changed.
