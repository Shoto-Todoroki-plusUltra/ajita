import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import os from "node:os";
import { preset } from "../../src/App";
const evidenceDir = process.env.QWS_EVIDENCE_DIR ?? "../evidence/checkpoint1c";

async function solve(page: Page, name: string) {
  const pending = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/problems/tsp/solve") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Solve and verify" }).click();
  const response = await pending;
  await fs.writeFile(
    `${evidenceDir}/browser-${name}.json`,
    JSON.stringify(
      { status: response.status(), body: await response.json() },
      null,
      2,
    ) + "\n",
  );
  return response;
}
test.beforeEach(async ({ page }) => {
  await page.goto("/");
});
test.beforeAll(async ({ browser }) => {
  await fs.writeFile(
    `${evidenceDir}/browser-environment.json`,
    JSON.stringify(
      {
        browser_version: browser.version(),
        node: process.version,
        platform: process.platform,
        architecture: process.arch,
        os_release: os.release(),
        recorded_at_utc: new Date().toISOString(),
        fixture_policy:
          "E2E uses real loopback backend; no route interception, mocked success or classical fallback",
      },
      null,
      2,
    ) + "\n",
  );
});
test("real classical preset and coordinate flows", async ({ page }) => {
  await page.getByLabel("Solver method").selectOption("exact_tsp");
  const response = await solve(page, "exact");
  expect(response.status()).toBe(200);
  await expect(
    page.getByRole("heading", { name: "Verified feasible tour" }),
  ).toBeVisible();
  expect((await response.json()).objective).toBe(4);
  await page.screenshot({
    path: `${evidenceDir}/classical-desktop.png`,
    fullPage: true,
  });
  await page.getByLabel("Solver method").selectOption("ortools_tsp");
  expect((await solve(page, "ortools")).status()).toBe(200);
  await page.getByRole("button", { name: "Planar coordinate example" }).click();
  expect((await solve(page, "coordinates")).status()).toBe(200);
  await expect(
    page.getByText("Planar coordinate sketch; Euclidean costs, not roads."),
  ).toBeVisible();
});
test("real local QAOA with trace honesty fields", async ({ page }) => {
  await page.getByLabel("Solver method").selectOption("quantum_local");
  const response = await solve(page, "quantum");
  expect(response.status()).toBe(200);
  const r = await response.json();
  expect(r.execution_status).toBe("completed");
  expect(r.quantum.raw_shots).toBe(4096);
  expect(r.quantum.feasible_shots + r.quantum.invalid_shots).toBe(4096);
  await expect(
    page.getByText("Total shots across optimizer evaluations"),
  ).toBeVisible();
  await expect(
    page.getByText("Optimizer success / convergence flag"),
  ).toBeVisible();
  await expect(
    page.getByText(/not a claim about sampling at final optimizer parameters/),
  ).toBeVisible();
  await page.screenshot({
    path: `${evidenceDir}/quantum-desktop.png`,
    fullPage: true,
  });
});
test("real no-feasible-sample and timeout states", async ({ page }) => {
  await page.getByLabel("Solver method").selectOption("quantum_local");
  await page.getByLabel("Shots per evaluation").fill("1");
  await page.getByLabel("Optimizer evaluations").fill("4");
  const r = await (await solve(page, "no-feasible")).json();
  expect(r.execution_status).toBe("completed");
  expect(r.quantum.feasible_shots).toBe(0);
  await expect(
    page.getByRole("heading", { name: "No feasible sample" }),
  ).toBeVisible();
  await page.getByLabel("Solver method").selectOption("exact_tsp");
  await page.getByLabel("Whole-work deadline (seconds)").fill("0.001");
  const timeout = await solve(page, "timeout");
  expect(timeout.status()).toBe(504);
  await expect(page.getByRole("alert")).toContainText("timeout");
});
test("invalid and oversized instances have no fabricated route", async ({
  page,
}) => {
  const bad = structuredClone(preset);
  if (bad.geometry.kind === "matrix") bad.geometry.distances[0][1] = 23;
  await page.getByLabel(/Instance JSON/).fill(JSON.stringify(bad));
  expect((await solve(page, "invalid")).status()).toBe(422);
  await expect(page.getByRole("alert")).toContainText("invalid_input");
  const ids = Array.from({ length: 9 }, (_, i) => String.fromCharCode(65 + i));
  const large = {
    ...preset,
    city_ids: ids,
    geometry: {
      kind: "matrix",
      distances: ids.map((_, i) => ids.map((_, j) => (i === j ? 0 : 1))),
    },
  };
  await page.getByLabel(/Instance JSON/).fill(JSON.stringify(large));
  await page.getByLabel("Solver method").selectOption("exact_tsp");
  expect((await solve(page, "oversized")).status()).toBe(400);
  await expect(page.getByRole("alert")).toContainText("unsupported_size");
  await expect(
    page.getByRole("heading", { name: "Verified feasible tour" }),
  ).toHaveCount(0);
});
test("small viewport remains usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: "Solve and verify" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${evidenceDir}/mobile-layout.png`,
    fullPage: true,
  });
});

test("real cancellation releases admission after worker cleanup", async ({
  page,
}) => {
  await page.getByLabel("Solver method").selectOption("quantum_local");
  await page.getByLabel("Shots per evaluation").fill("128");
  await page.getByLabel("Optimizer evaluations").fill("50");
  await page.getByRole("button", { name: "Solve and verify" }).click();
  await expect
    .poll(
      async () => (await (await page.request.get("/api/health")).json()).busy,
    )
    .toBe(true);
  const refused = await page.request.post("/api/problems/tsp/solve", {
    data: { instance: preset, solver: "exact_tsp" },
  });
  expect(refused.status()).toBe(503);
  expect((await refused.json()).error.code).toBe("busy");
  await page.getByRole("button", { name: "Cancel request" }).click();
  await expect(page.getByRole("alert")).toContainText("Request cancelled");
  await expect
    .poll(
      async () => (await (await page.request.get("/api/health")).json()).busy,
    )
    .toBe(false);
  const recovered = await page.request.post("/api/problems/tsp/solve", {
    data: { instance: preset, solver: "exact_tsp", timeout_s: 20.0 },
  });
  expect(recovered.status()).toBe(200);
  const r = await recovered.json();
  expect(r.worker.worker_alive_after_cleanup).toBe(false);
  await fs.writeFile(
    `${evidenceDir}/browser-cancellation.json`,
    JSON.stringify(
      {
        refused_status: refused.status(),
        refused_body: await refused.json(),
        recovered_status: recovered.status(),
        recovered_body: r,
      },
      null,
      2,
    ) + "\n",
  );
});

test("fixture reference follows current input, not its ID or previous solve", async ({
  page,
}) => {
  await expect(
    page.getByRole("heading", { name: "Uniform random nine-bit sampling" }),
  ).toBeVisible();
  await page.getByLabel("Solver method").selectOption("quantum_local");
  await page.getByLabel("Shots per evaluation").fill("1");
  await page.getByLabel("Optimizer evaluations").fill("4");
  expect((await solve(page, "baseline-preset")).status()).toBe(200);
  await expect(page.getByText(/With 4 independent draws/)).toBeVisible();
  const edited = structuredClone(preset);
  if (edited.geometry.kind === "matrix") {
    edited.geometry.distances[0][1] = 3;
    edited.geometry.distances[1][0] = 3;
  }
  await page.getByLabel(/Instance JSON/).fill(JSON.stringify(edited));
  await expect(page.getByText(/No analytical uniform baseline/)).toBeVisible();
  await expect(
    page.getByText(
      /512 equally likely|two attain cost 4|With 4 independent draws/,
    ),
  ).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Solve result" })).toHaveCount(
    0,
  );
  await page.getByLabel("Solver method").selectOption("exact_tsp");
  expect((await solve(page, "baseline-edited-same-id")).status()).toBe(200);
  await expect(
    page.getByRole("heading", { name: "Uniform random nine-bit sampling" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Planar coordinate example" }).click();
  await expect(page.getByText(/No analytical uniform baseline/)).toBeVisible();
  expect((await solve(page, "baseline-coordinates")).status()).toBe(200);
  await expect(
    page.getByText(/512 equally likely|two attain cost 4/),
  ).toHaveCount(0);
  const ids = ["A", "B", "C", "D", "E"];
  const five = {
    ...preset,
    city_ids: ids,
    geometry: {
      kind: "matrix",
      distances: ids.map((_, i) => ids.map((_, j) => (i === j ? 0 : 1))),
    },
  };
  await page.getByLabel(/Instance JSON/).fill(JSON.stringify(five));
  expect((await solve(page, "baseline-five-city")).status()).toBe(200);
  await expect(page.getByText(/No analytical uniform baseline/)).toBeVisible();
  await expect(
    page.getByText(/512 equally likely|two attain cost 4/),
  ).toHaveCount(0);
  await page.screenshot({
    path: `${evidenceDir}/baseline-neutral.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Four-city matrix preset" }).click();
  await expect(
    page.getByRole("heading", { name: "Uniform random nine-bit sampling" }),
  ).toBeVisible();
});
