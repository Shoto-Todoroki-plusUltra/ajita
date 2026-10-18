#!/bin/sh
set -eu
# Run from repository root with the pinned Node LTS on PATH.
QWS_PYTHON="${QWS_PYTHON:-.venv-api/bin/python}"
"$QWS_PYTHON" -m ruff check src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py src/quantum_workload_studio/cli.py
"$QWS_PYTHON" -m ruff format --check src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py
"$QWS_PYTHON" -m ruff check scripts/audit_cold_start.py scripts/create_review_archive.py tests/test_review_archive.py
"$QWS_PYTHON" -m ruff format --check scripts/audit_cold_start.py scripts/create_review_archive.py tests/test_review_archive.py
"$QWS_PYTHON" scripts/export_openapi.py --check
npm --prefix frontend run types:check
npm --prefix frontend run format:check

"$QWS_PYTHON" -m ruff check src/quantum_workload_studio/models/timetable.py src/quantum_workload_studio/classical/timetable.py src/quantum_workload_studio/qubo/timetable.py src/quantum_workload_studio/domains/timetable.py src/quantum_workload_studio/timetable_cli.py scripts/evidence_timetable.py tests/test_timetable.py
"$QWS_PYTHON" -m ruff format --check src/quantum_workload_studio/models/timetable.py src/quantum_workload_studio/classical/timetable.py src/quantum_workload_studio/qubo/timetable.py src/quantum_workload_studio/domains/timetable.py src/quantum_workload_studio/timetable_cli.py scripts/evidence_timetable.py tests/test_timetable.py
