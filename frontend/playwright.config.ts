import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  expect: { timeout: 40000 },
  retries: 0,
  reporter: [
    ["list"],
    [
      "junit",
      {
        outputFile: `${process.env.QWS_EVIDENCE_DIR ?? "../evidence/checkpoint1c"}/playwright.xml`,
      },
    ],
  ],
  use: { baseURL: "http://127.0.0.1:5173", trace: "retain-on-failure" },
  projects: [{ name: "chromium-mac", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command:
        "QWS_ENABLE_LOCAL_QUANTUM=1 ../.venv-api-quantum/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 60000,
      reuseExistingServer: false,
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:5173",
      timeout: 60000,
      reuseExistingServer: false,
    },
  ],
});
