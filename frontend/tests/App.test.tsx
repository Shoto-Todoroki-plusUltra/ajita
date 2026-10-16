import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { App, Results, uniformReference, type Result } from "../src/App";

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
