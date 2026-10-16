#!/bin/sh
set -eu
# Run from repository root with the pinned Node LTS on PATH.
QWS_PYTHON="${QWS_PYTHON:-.venv-api/bin/python}"
"$QWS_PYTHON" -m ruff check src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py src/quantum_workload_studio/cli.py
"$QWS_PYTHON" -m ruff format --check src/quantum_workload_studio/api src/quantum_workload_studio/services tests/api scripts/export_openapi.py
"$QWS_PYTHON" scripts/export_openapi.py --check
npm --prefix frontend run types:check
npm --prefix frontend run format:check
