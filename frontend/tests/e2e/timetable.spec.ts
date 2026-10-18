import { test, expect, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import { timetablePreset } from "../../src/Timetable";
const dir = process.env.QWS_EVIDENCE_DIR ?? "../evidence/phase2";
async function act(
  page: Page,
  operation: string,
  button: string,
  name: string,
) {
  const pending = page.waitForResponse(
    (r) =>
      r.url().endsWith(`/api/problems/timetable/${operation}`) &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: button, exact: true }).click();
  const response = await pending;
  await fs.writeFile(
    `${dir}/browser-b1-${name}.json`,
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
  await page.getByRole("button", { name: "Classroom timetable" }).click();
});
test("real CP-SAT and exhaustive oracle grid", async ({ page }) => {
  const r = await act(page, "solve", "Solve timetable", "cp-sat");
  expect(r.status()).toBe(200);
  const data = await r.json();
  expect(data.result.objective).toBe(1);
  expect(data.result.native_status).toBe("OPTIMAL");
  await expect(
    page.getByRole("table", { name: "Verified timetable grid" }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Math", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "Physics", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/512 equally likely|Uniform random nine-bit/),
  ).toHaveCount(0);
  await page.screenshot({ path: `${dir}/timetable-grid.png`, fullPage: true });
  await page.getByLabel("Timetable solver").selectOption("enumeration");
  const exact = await act(page, "solve", "Solve timetable", "enumeration");
  expect((await exact.json()).result.objective).toBe(1);
  await page.getByLabel("Timetable instance JSON").fill("{}");
  await expect(page.getByRole("table")).toHaveCount(0);
});
test("real QUBO feasible and invalid candidates with conflict reasons", async ({
  page,
}) => {
  const q = await act(page, "compile", "Compile B1 QUBO", "compile");
  expect(q.status()).toBe(200);
  expect((await q.json()).variables.length).toBe(4);
  await page
    .getByLabel("B1 candidate bits (leftmost is variable 0)")
    .fill("1010");
  const invalid = await act(
    page,
    "inspect",
    "Inspect B1 candidate",
    "invalid-bits",
  );
  expect((await invalid.json()).validation.feasible).toBe(false);
  await expect(page.getByText(/room_conflict:/)).toBeVisible();
  await expect(page.getByText(/lecturer_conflict:/)).toBeVisible();
  await expect(page.getByText(/cohort_conflict:/)).toBeVisible();
  await page
    .getByLabel("B1 candidate bits (leftmost is variable 0)")
    .fill("1001");
  expect(
    (
      await (
        await act(page, "inspect", "Inspect B1 candidate", "feasible-bits")
      ).json()
    ).original_objective,
  ).toBe(1);
  await expect(
    page.getByText(/No timetable quantum experiment is executed/),
  ).toBeVisible();
});
test("real infeasible, invalid, timeout and unsupported states", async ({
  page,
}) => {
  const i = structuredClone(timetablePreset);
  i.rooms[0].capacity = 0;
  await page.getByLabel("Timetable instance JSON").fill(JSON.stringify(i));
  const infeasible = await act(page, "solve", "Solve timetable", "infeasible");
  expect((await infeasible.json()).result.native_status).toBe("INFEASIBLE");
  await expect(page.getByRole("table")).toHaveCount(0);
  i.courses[0].lecturer_id = "missing";
  await page.getByLabel("Timetable instance JSON").fill(JSON.stringify(i));
  expect(
    (await act(page, "solve", "Solve timetable", "invalid")).status(),
  ).toBe(422);
  await page.getByRole("button", { name: "Two-course B1 preset" }).click();
  await page
    .getByLabel("Timetable whole-work deadline (seconds)")
    .fill("0.001");
  expect(
    (await act(page, "solve", "Solve timetable", "timeout")).status(),
  ).toBe(504);
  await expect(page.getByRole("alert")).toContainText("timeout");
  const large = structuredClone(timetablePreset);
  large.preferences = [];
  large.slots = Array.from({ length: 10 }, (_, k) => ({
    id: `s${k}`,
    label: String(k),
    order: k,
  }));
  await page.getByLabel("Timetable instance JSON").fill(JSON.stringify(large));
  expect(
    (await act(page, "compile", "Compile B1 QUBO", "oversized")).status(),
  ).toBe(400);
  await expect(page.getByRole("alert")).toContainText("unsupported_size");
});
test("small B1 viewport and module switch", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("button", { name: "Solve timetable" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${dir}/timetable-mobile.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "TSP", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Uniform random nine-bit sampling" }),
  ).toBeVisible();
});
