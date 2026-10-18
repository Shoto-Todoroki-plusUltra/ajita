import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import {
  App,
  AnalyticalReference,
  Results,
  preset,
  uniformReference,
  type Result,
} from "../src/App";

// Explicit unit fixtures; these are never used by the application or evidence runs.
const noFeasible: Result = {
  schema_version: 1,
  instance_hash: "unit-fixture",
  method: "quantum_local",
  solver_id: "statevector",
  execution_status: "completed",
  outcome: "no_feasible_sample",
  assignment: null,
  validation: { checked: false, feasible: null, violations: [] },
  objective: null,
  objective_unit: "synthetic_cost",
  proven_optimal: false,
  total_elapsed_s: 0.5,
  worker: { worker_exitcode: 0, forced_cleanup: false },
  effective_options: {},
  quantum: {
    raw_shots: 4,
    evaluations: 4,
    feasible_shots: 0,
    invalid_shots: 4,
    feasible_fraction: 0,
    invalid_fraction: 1,
    candidate_outcome: "no_feasible_sample",
    optimizer_success: false,
    optimizer_message: "unit fixture budget",
    exact_reference: 4,
    absolute_gap: null,
    raw_counts: { "000000000": 4 },
    selection_policy: "entire trace",
  },
};
describe("honest presentation", () => {
  it("never prefills a result", () => {
    render(<App />);
    expect(screen.getByText(/No solution is prefilled/)).toBeInTheDocument();
    expect(
      screen.queryByText("Verified feasible tour"),
    ).not.toBeInTheDocument();
  });
  it("shows no-feasible state and separate convergence flag", () => {
    render(<Results result={noFeasible} />);
    expect(
      screen.getByRole("heading", { name: "No feasible sample" }),
    ).toBeInTheDocument();
    expect(screen.getByText("false")).toBeInTheDocument();
    expect(
      screen.getByText("Backend computation elapsed (including cleanup)"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/HTTP, network and browser latency are not included/),
    ).toBeInTheDocument();
    expect(screen.getByText("0.0000% / 100.0000%")).toBeInTheDocument();
    expect(screen.getByText(/final optimizer parameters/)).toBeInTheDocument();
    expect(
      screen.getByText(/Unavailable — no feasible sample/),
    ).toBeInTheDocument();
  });
  it("uses exact analytical uniform probabilities", () => {
    const r = uniformReference(4096);
    expect(r.expectedFeasible).toBe(48);
    expect(r.expectedOptimal).toBe(16);
    expect(r.feasibleProbability).toBe(6 / 512);
  });
  it("shows server errors without a fabricated solution", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: { code: "unsupported_size", message: "too many variables" },
        }),
      }),
    );
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Solve and verify" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "unsupported_size",
    );
    expect(
      screen.queryByText("Verified feasible tour"),
    ).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

describe("fixture-specific analytical reference", () => {
  const numbers =
    /512 equally likely|six are feasible|two attain cost 4|48\.000|16\.000/;
  it("shows expectations only for the unchanged original preset", () => {
    const reordered = Object.fromEntries(Object.entries(preset).reverse());
    render(
      <AnalyticalReference input={JSON.stringify(reordered)} shots={4096} />,
    );
    expect(
      screen.getByRole("heading", { name: "Uniform random nine-bit sampling" }),
    ).toBeInTheDocument();
    expect(screen.getByText(numbers)).toBeInTheDocument();
    expect(
      screen.getByText(/not an executed random run or a quantum benchmark/),
    ).toBeInTheDocument();
  });
  it("hides preset numbers for an edited matrix with the same ID", async () => {
    render(<App />);
    const edited = structuredClone(preset);
    if (edited.geometry.kind === "matrix") {
      edited.geometry.distances[0][1] = 3;
      edited.geometry.distances[1][0] = 3;
    }
    await userEvent.clear(screen.getByLabelText(/Instance JSON/));
    // Paste-like change avoids a per-character UI run; this is a unit input event.
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.change(screen.getByLabelText(/Instance JSON/), {
      target: { value: JSON.stringify(edited) },
    });
    expect(
      screen.getByText(/No analytical uniform baseline/),
    ).toBeInTheDocument();
    expect(screen.queryByText(numbers)).not.toBeInTheDocument();
    expect(
      screen.queryByText("Uniform random nine-bit sampling"),
    ).not.toBeInTheDocument();
  });
  it("hides numbers for the actual coordinate example control", async () => {
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Planar coordinate example" }),
    );
    expect(
      screen.getByText(/No analytical uniform baseline/),
    ).toBeInTheDocument();
    expect(screen.queryByText(numbers)).not.toBeInTheDocument();
  });
  it("hides numbers for five-city matrices", () => {
    const ids = ["A", "B", "C", "D", "E"];
    const five = {
      ...preset,
      city_ids: ids,
      geometry: {
        kind: "matrix",
        distances: ids.map((_, i) => ids.map((_, j) => (i === j ? 0 : 1))),
      },
    };
    render(<AnalyticalReference input={JSON.stringify(five)} shots={4096} />);
    expect(
      screen.getByText(/No analytical uniform baseline/),
    ).toBeInTheDocument();
    expect(screen.queryByText(numbers)).not.toBeInTheDocument();
  });
  it("clears previous sampled-shot figures as soon as input is edited", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => noFeasible }),
    );
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Solve and verify" }),
    );
    await screen.findByRole("heading", { name: "No feasible sample" });
    expect(screen.getByText(/With 4 independent draws/)).toBeInTheDocument();
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.change(screen.getByLabelText(/Instance JSON/), {
      target: { value: "{}" },
    });
    expect(
      screen.queryByRole("heading", { name: "No feasible sample" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/With 4 independent draws/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(numbers)).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(
      screen.getByText(/No analytical uniform baseline/),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
