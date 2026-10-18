# Phase 2 review inventory

Baseline: accepted targeted 1C source `2f66cdf`. Required hidden files are included in the full source archive. `.github/workflows/checks.yml` adds the B1 classical selection; `.gitignore` and `.githooks/pre-commit` are preserved. Existing locks and historical evidence are byte-identical (126 files audited). The pre-existing untracked root `ARCHIVE_MANIFEST.json` is intentionally excluded and untouched.

| Area | Review files |
| --- | --- |
| Original domain and seven-method adapter | `src/quantum_workload_studio/models/timetable.py`, `domains/timetable.py` |
| Independent oracle / native CP-SAT | `classical/timetable.py` |
| Bounded QUBO / canonical import / decode | `qubo/timetable.py` |
| Service / worker / CLI | `services/timetable.py`, `timetable_cli.py`, small dispatch addition in `cli.py` |
| Typed HTTP integration | `api/timetable.py`, route registration in `api/app.py`, `schemas/openapi.json` |
| Minimal UI | `frontend/src/Timetable.tsx`, module navigation/abort cleanup in `App.tsx`, small styles, generated `api.generated.ts` |
| Tests | `tests/test_timetable.py`, `tests/api/test_timetable_service.py`, `frontend/tests/Timetable.test.tsx`, `frontend/tests/e2e/timetable.spec.ts` |
| Reproduction | `examples/timetable/tiny.json`, `scripts/evidence_timetable.py`, `scripts/audit_phase2_preservation.py`, quality script and CI selection |
| Evidence/report | This directory, README, architecture/decisions/phase plan and implementation report |

Only the first Python path above includes the package prefix; other Python module paths in this table are relative to `src/quantum_workload_studio/`. The exact archive member/digest inventory is the ZIP's external `.zip.manifest.json`, including the embedded manifest. This list identifies changed/new project files, not every unchanged member retained in the full archive. No environments/modules/caches/Git internals or unrelated root manifest are included.

## Changed and new files relative to accepted baseline

- `.github/workflows/checks.yml`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DECISIONS.md`
- `docs/IMPLEMENTATION_REPORT.md`
- `docs/PHASE_PLAN.md`
- `evidence/phase2/FILE_INVENTORY.md`
- `evidence/phase2/acceptance-summary.json`
- `evidence/phase2/api-initial.log`
- `evidence/phase2/api-initial.xml`
- `evidence/phase2/api.log`
- `evidence/phase2/api.xml`
- `evidence/phase2/backend-final.log`
- `evidence/phase2/backend-final.xml`
- `evidence/phase2/backend-targeted-collection-failure.log`
- `evidence/phase2/backend-targeted-collection-failure.xml`
- `evidence/phase2/backend-targeted.log`
- `evidence/phase2/backend-targeted.xml`
- `evidence/phase2/baseline-neutral.png`
- `evidence/phase2/browser-b1-compile.json`
- `evidence/phase2/browser-b1-cp-sat.json`
- `evidence/phase2/browser-b1-enumeration.json`
- `evidence/phase2/browser-b1-feasible-bits.json`
- `evidence/phase2/browser-b1-infeasible.json`
- `evidence/phase2/browser-b1-invalid-bits.json`
- `evidence/phase2/browser-b1-invalid.json`
- `evidence/phase2/browser-b1-oversized.json`
- `evidence/phase2/browser-b1-timeout.json`
- `evidence/phase2/browser-baseline-coordinates.json`
- `evidence/phase2/browser-baseline-edited-same-id.json`
- `evidence/phase2/browser-baseline-five-city.json`
- `evidence/phase2/browser-baseline-preset.json`
- `evidence/phase2/browser-cancellation.json`
- `evidence/phase2/browser-coordinates.json`
- `evidence/phase2/browser-environment.json`
- `evidence/phase2/browser-exact.json`
- `evidence/phase2/browser-invalid.json`
- `evidence/phase2/browser-no-feasible.json`
- `evidence/phase2/browser-ortools.json`
- `evidence/phase2/browser-oversized.json`
- `evidence/phase2/browser-quantum.json`
- `evidence/phase2/browser-timeout.json`
- `evidence/phase2/classical-desktop.png`
- `evidence/phase2/classical-macos-intermediate.log`
- `evidence/phase2/classical-macos-intermediate.xml`
- `evidence/phase2/classical-macos.log`
- `evidence/phase2/classical-macos.xml`
- `evidence/phase2/cli-cp-sat.json`
- `evidence/phase2/cli-enumeration.json`
- `evidence/phase2/cli-inspection.json`
- `evidence/phase2/cli-qubo.json`
- `evidence/phase2/commands.md`
- `evidence/phase2/environment-and-preservation.json`
- `evidence/phase2/frontend-build-final.log`
- `evidence/phase2/frontend-build-initial.log`
- `evidence/phase2/frontend-build.log`
- `evidence/phase2/frontend-format-final.log`
- `evidence/phase2/frontend-format.log`
- `evidence/phase2/full-macos-quantum-intermediate.log`
- `evidence/phase2/full-macos-quantum-intermediate.xml`
- `evidence/phase2/full-macos-quantum.log`
- `evidence/phase2/full-macos-quantum.xml`
- `evidence/phase2/math-capacity-infeasible.json`
- `evidence/phase2/math-feasible.json`
- `evidence/phase2/math-shared-slot-infeasible.json`
- `evidence/phase2/math-ties.json`
- `evidence/phase2/mathematical-core-initial-collection-failure.log`
- `evidence/phase2/mathematical-core-initial-collection-failure.xml`
- `evidence/phase2/mathematical-core.log`
- `evidence/phase2/mathematical-core.xml`
- `evidence/phase2/mathematical-evidence.log`
- `evidence/phase2/mathematical-summary.json`
- `evidence/phase2/mobile-layout.png`
- `evidence/phase2/packages-classical.json`
- `evidence/phase2/packages-quantum.json`
- `evidence/phase2/pip-check-classical.log`
- `evidence/phase2/pip-check-quantum.log`
- `evidence/phase2/playwright-final.log`
- `evidence/phase2/playwright-initial.log`
- `evidence/phase2/playwright.log`
- `evidence/phase2/playwright.xml`
- `evidence/phase2/quality-final.log`
- `evidence/phase2/quality.log`
- `evidence/phase2/quantum-desktop.png`
- `evidence/phase2/timetable-grid.png`
- `evidence/phase2/timetable-mobile.png`
- `evidence/phase2/vitest-final.log`
- `evidence/phase2/vitest.log`
- `evidence/phase2/vitest.xml`
- `examples/timetable/tiny.json`
- `frontend/src/App.tsx`
- `frontend/src/Timetable.tsx`
- `frontend/src/api.generated.ts`
- `frontend/src/style.css`
- `frontend/tests/Timetable.test.tsx`
- `frontend/tests/e2e/timetable.spec.ts`
- `schemas/openapi.json`
- `scripts/audit_phase2_preservation.py`
- `scripts/check_quality.sh`
- `scripts/evidence_timetable.py`
- `src/quantum_workload_studio/api/app.py`
- `src/quantum_workload_studio/api/timetable.py`
- `src/quantum_workload_studio/classical/timetable.py`
- `src/quantum_workload_studio/cli.py`
- `src/quantum_workload_studio/domains/timetable.py`
- `src/quantum_workload_studio/models/timetable.py`
- `src/quantum_workload_studio/qubo/timetable.py`
- `src/quantum_workload_studio/services/timetable.py`
- `src/quantum_workload_studio/timetable_cli.py`
- `tests/api/test_timetable_service.py`
- `tests/test_timetable.py`
