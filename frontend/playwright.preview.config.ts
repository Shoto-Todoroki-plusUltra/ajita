// Admissions-only selection: no sampler or quantum-cancellation flows.
import { defineConfig } from "@playwright/test";
import base from "./playwright.config";
export default defineConfig({
  ...base,
  grepInvert:
    /real local QAOA|real no-feasible-sample and timeout|real cancellation releases|fixture reference follows current input/,
  webServer: [
    {
      command:
        "QWS_ENABLE_LOCAL_QUANTUM=0 PYTHONPATH=../src ../.venv-api/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 60000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      timeout: 60000,
      reuseExistingServer: true,
    },
  ],
});
