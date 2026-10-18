import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { Timetable } from "../src/Timetable";

describe("B1 presentation", () => {
  it("offers a separate module without TSP fixture statistics", async () => {
    render(<App />);
    await userEvent.click(
      screen.getByRole("button", { name: "Classroom timetable" }),
    );
    expect(screen.getByText(/No timetable is prefilled/)).toBeInTheDocument();
    expect(
      screen.queryByText(
        /512 equally likely|six are feasible|Uniform random nine-bit/,
      ),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Historical OR-Tools/)).toBeInTheDocument();
  });
  it("clears QUBO and candidate evidence on edited input", async () => {
    // Explicit unit response, never an executed experiment or production result.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          variables: [],
          penalty: 1,
          soft_upper_bound: 0,
          penalty_sufficient: true,
          offset: 2,
          scale: 1,
        }),
      }),
    );
    render(<Timetable />);
    await userEvent.click(
      screen.getByRole("button", { name: "Compile B1 QUBO" }),
    );
    await screen.findByRole("region", { name: "B1 QUBO" });
    expect(
      screen.getByText(/No timetable quantum experiment is executed/),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Timetable instance JSON"), {
      target: { value: "{}" },
    });
    expect(
      screen.queryByRole("region", { name: "B1 QUBO" }),
    ).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });
  it("retains structured errors without fabricated grid", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: { code: "timeout", message: "worker exceeded deadline" },
        }),
      }),
    );
    render(<Timetable />);
    await userEvent.click(
      screen.getByRole("button", { name: "Solve timetable" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("timeout");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
