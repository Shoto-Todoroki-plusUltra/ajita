import { useEffect, useRef, useState } from "react";
import type { components } from "./api.generated";

type Instance = components["schemas"]["TimetableInstance"];
type Result = components["schemas"]["Result"];
type Qubo = components["schemas"]["TimetableQubo"];
type Inspection = components["schemas"]["Inspection"];
export const timetablePreset: Instance = {
  schema_version: 1,
  kind: "timetable",
  instance_id: "b1-two-courses",
  rooms: [{ id: "R1", capacity: 30 }],
  slots: [
    { id: "S1", label: "Monday 09:00", order: 0 },
    { id: "S2", label: "Monday 10:00", order: 1 },
  ],
  lecturer_ids: ["L1"],
  cohort_ids: ["G1"],
  courses: [
    { id: "Math", lecturer_id: "L1", cohort_ids: ["G1"], enrollment: 20 },
    { id: "Physics", lecturer_id: "L1", cohort_ids: ["G1"], enrollment: 25 },
  ],
  preferences: [
    { course_id: "Math", room_id: "R1", slot_id: "S2", penalty: 3 },
    { course_id: "Physics", room_id: "R1", slot_id: "S1", penalty: 2 },
    { course_id: "Physics", room_id: "R1", slot_id: "S2", penalty: 1 },
  ],
};

export function Timetable() {
  const [input, setInput] = useState(JSON.stringify(timetablePreset, null, 2));
  const [solver, setSolver] = useState<"cp_sat" | "enumeration">("cp_sat");
  const [deadline, setDeadline] = useState(20);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [solved, setSolved] = useState<Instance | null>(null);
  const [qubo, setQubo] = useState<Qubo | null>(null),
    [bits, setBits] = useState("");
  const [inspection, setInspection] = useState<Inspection | null>(null);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  function change(value: string) {
    setInput(value);
    setResult(null);
    setSolved(null);
    setQubo(null);
    setInspection(null);
    setBits("");
    setError("");
  }
  async function request(operation: "solve" | "compile" | "inspect") {
    setError("");
    let instance: Instance;
    try {
      instance = JSON.parse(input);
    } catch {
      setError("Invalid timetable JSON");
      return;
    }
    if (operation === "solve") {
      setResult(null);
      setSolved(null);
    }
    if (operation === "compile") {
      setQubo(null);
      setInspection(null);
    }
    if (operation === "inspect") setInspection(null);
    controller.current = new AbortController();
    setBusy(true);
    try {
      const body =
        operation === "solve"
          ? {
              instance,
              solver,
              timeout_s: deadline,
              memory_limit_mb: 512,
              seed: 1729,
            }
          : operation === "compile"
            ? { instance }
            : { instance, qubo, bits };
      const response = await fetch(`/api/problems/timetable/${operation}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.current.signal,
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          `${data.error?.code}: ${data.error?.message}${data.error?.details?.length ? " — " + JSON.stringify(data.error.details) : ""}`,
        );
      if (operation === "solve") {
        setResult(data);
        setSolved(instance);
      } else if (operation === "compile") {
        setQubo(data);
        setBits("0".repeat(data.variables.length));
      } else setInspection(data);
    } catch (e) {
      setError(
        e instanceof Error && e.name === "AbortError"
          ? "Request cancelled; server worker cleanup may briefly keep admission busy."
          : String(e instanceof Error ? e.message : e),
      );
    } finally {
      setBusy(false);
      controller.current = null;
    }
  }
  return (
    <main>
      <header>
        <p className="eyebrow">QUANTUM WORKLOAD STUDIO / B1 CLASSROOMS</p>
        <h1>
          One course. One slot.
          <br />A checked timetable.
        </h1>
        <p>
          Discrete nonoverlapping slots, room capacities, lecturer and cohort
          conflicts. No recurrence or individual student sectioning.
        </p>
        <p className="disclaimer">
          Research prototype · No quantum acceleration or novelty established ·
          Unlicensed and unpublished
        </p>
      </header>
      <div className="workspace">
        <section className="editor">
          <h2>1. Define the timetable</h2>
          <button
            disabled={busy}
            onClick={() => change(JSON.stringify(timetablePreset, null, 2))}
          >
            Two-course B1 preset
          </button>
          <label htmlFor="timetable-input">Timetable instance JSON</label>
          <textarea
            id="timetable-input"
            value={input}
            disabled={busy}
            spellCheck={false}
            onChange={(e) => change(e.target.value)}
          />
          <label htmlFor="timetable-solver">Timetable solver</label>
          <select
            id="timetable-solver"
            disabled={busy}
            value={solver}
            onChange={(e) => {
              setSolver(e.target.value as typeof solver);
              setResult(null);
              setSolved(null);
            }}
          >
            <option value="cp_sat">Classical · OR-Tools CP-SAT</option>
            <option value="enumeration">
              Classical · tiny exhaustive oracle
            </option>
          </select>
          <label>
            Timetable whole-work deadline (seconds)
            <input
              type="number"
              min="0.001"
              max="60"
              step="0.001"
              disabled={busy}
              value={deadline}
              onChange={(e) => setDeadline(+e.target.value)}
            />
          </label>
          <div className="buttons">
            <button
              className="primary"
              disabled={busy}
              onClick={() => void request("solve")}
            >
              Solve timetable
            </button>
            <button disabled={busy} onClick={() => void request("compile")}>
              Compile B1 QUBO
            </button>
            {busy && (
              <button onClick={() => controller.current?.abort()}>
                Cancel timetable request
              </button>
            )}
          </div>
          <p className="muted">
            One worker shared with TSP; sampled RSS monitoring is not a hard
            memory guarantee. Historical OR-Tools startup/tail-latency timeouts
            remain unresolved.
          </p>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>
        <section className="answer">
          <h2>2. Inspect the timetable</h2>
          {!result && (
            <p>
              No timetable is prefilled. Solve to obtain a validated result.
            </p>
          )}
          {result && (
            <section aria-label="Timetable result">
              <p role="status">
                Native solver status:{" "}
                <strong>{result.result.native_status}</strong>
              </p>
              <dl className="metrics">
                <div>
                  <dt>Original preference objective</dt>
                  <dd>{result.result.objective ?? "Unavailable"}</dd>
                </div>
                <div>
                  <dt>
                    {result.result.solver_id === "cp_sat"
                      ? "Native best objective bound"
                      : "Exhaustive oracle bound"}
                  </dt>
                  <dd>{result.result.best_objective_bound ?? "Unavailable"}</dd>
                </div>
                <div>
                  <dt>Proven optimal / infeasible</dt>
                  <dd>
                    {String(result.result.proven_optimal)} /{" "}
                    {String(result.result.proven_infeasible)}
                  </dd>
                </div>
                <div>
                  <dt>Backend computation elapsed (including cleanup)</dt>
                  <dd>
                    {result.backend_computation_elapsed_s.toFixed(4)} seconds
                  </dd>
                </div>
                <div>
                  <dt>Model and solver elapsed</dt>
                  <dd>{result.result.solver_elapsed_s.toFixed(4)} seconds</dd>
                </div>
              </dl>
              <p>
                HTTP, network and browser latency are excluded. FEASIBLE is not
                an optimality proof; UNKNOWN is not an infeasibility proof.
              </p>
              {result.result.assignment && solved && (
                <>
                  <p>
                    Original constraints:{" "}
                    {result.result.validation.feasible
                      ? "Verified feasible"
                      : "Invalid"}
                  </p>
                  <div className="table-scroll">
                    <table aria-label="Verified timetable grid">
                      <thead>
                        <tr>
                          <th>Slot</th>
                          {solved.rooms.map((r) => (
                            <th key={r.id}>{r.id}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[...solved.slots]
                          .sort((a, b) => a.order - b.order)
                          .map((s) => (
                            <tr key={s.id}>
                              <th>{s.label}</th>
                              {solved.rooms.map((r) => (
                                <td key={r.id}>
                                  {result.result
                                    .assignment!.assignments.filter(
                                      (p) =>
                                        p.slot_id === s.id &&
                                        p.room_id === r.id,
                                    )
                                    .map((p) => p.course_id)
                                    .join(", ") || "—"}
                                </td>
                              ))}
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
              {result.result.proven_infeasible && (
                <p>
                  Hard constraints proven infeasible by{" "}
                  {result.result.solver_id}. No candidate assignment or
                  preference objective is reported. Check capacity, available
                  slots and shared resources; no unsatisfiable-core explanation
                  is claimed.
                </p>
              )}
              <p className="muted">
                Worker exit: {String(result.worker.worker_exitcode)} · Forced
                cleanup: {String(result.worker.forced_cleanup)}
              </p>
            </section>
          )}
          {qubo && (
            <section aria-label="B1 QUBO">
              <h3>Optional B1 QUBO inspection</h3>
              <p>
                {qubo.variables.length} capacity-admissible variables · Penalty{" "}
                {qubo.penalty} &gt; soft upper bound {qubo.soft_upper_bound}:{" "}
                {String(qubo.penalty_sufficient)} · Offset {qubo.offset} · Scale{" "}
                {qubo.scale}
              </p>
              <p>
                Portable upper-triangular mathematical encoding only. No
                timetable quantum experiment is executed. No analytical uniform
                sampling baseline has been calculated for this instance.
              </p>
              <details>
                <summary>Canonical variables and coefficients</summary>
                <pre>{JSON.stringify(qubo, null, 2)}</pre>
              </details>
              <label htmlFor="timetable-bits">
                B1 candidate bits (leftmost is variable 0)
              </label>
              <input
                id="timetable-bits"
                value={bits}
                disabled={busy}
                maxLength={16}
                onChange={(e) => {
                  setBits(e.target.value);
                  setInspection(null);
                }}
              />
              <button disabled={busy} onClick={() => void request("inspect")}>
                Inspect B1 candidate
              </button>
              {inspection && (
                <section aria-label="B1 candidate result">
                  <p>QUBO energy: {inspection.energy}</p>
                  <p>
                    Candidate:{" "}
                    {inspection.validation.feasible
                      ? "Verified feasible"
                      : "Invalid"}{" "}
                    · Original preference objective:{" "}
                    {inspection.original_objective ?? "Unavailable"}
                  </p>
                  <ul>
                    {inspection.validation.violations.map((v, i) => (
                      <li key={i}>
                        {v.code}: {v.message} ({v.entity_ids.join(", ")})
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </section>
          )}
        </section>
      </div>
      <footer>
        Phase 2 · B1 classroom timetabling only · No cloud jobs or public
        release.
      </footer>
    </main>
  );
}
