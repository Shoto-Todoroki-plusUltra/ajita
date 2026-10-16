"""Export/check API schema without importing a quantum SDK."""

import argparse
import json
from pathlib import Path

from quantum_workload_studio.api.app import create_app

parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
path = Path(__file__).resolve().parents[1] / "schemas/openapi.json"
text = json.dumps(create_app().openapi(), sort_keys=True, indent=2, allow_nan=False) + "\n"
if args.check:
    if path.read_text() != text:
        raise SystemExit("OpenAPI schema drift; regenerate and review TypeScript types")
else:
    path.write_text(text)
