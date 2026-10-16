import { useRef, useState } from "react";
import type { components } from "./api.generated";

type Instance = components["schemas"]["TspInstance"];
export type Result = components["schemas"]["ApiResult"];
type SolveRequest = components["schemas"]["SolveRequest"];
export const preset: Instance = {
  schema_version: 1,
  kind: "tsp",
  instance_id: "four_city_synthetic_v1",
  city_ids: ["A", "B", "C", "D"],
  depot_id: "A",
  distance_unit: "synthetic_cost",
  geometry: {
    kind: "matrix",
    distances: [
      [0, 1, 2, 1],
      [1, 0, 1, 2],
      [2, 1, 0, 1],
      [1, 2, 1, 0],
    ],
  },
};

export function uniformReference(shots: number) {
  return {
    feasibleProbability: 6 / 512,
    optimalProbability: 2 / 512,
    expectedFeasible: (shots * 6) / 512,
    expectedOptimal: (shots * 2) / 512,
    atLeastOneFeasible: -Math.expm1(shots * Math.log1p(-6 / 512)),
  };
}
const percent = (value: number | null) =>
  value === null ? "Unavailable" : `${(value * 100).toFixed(4)}%`;

export function Tour({
  instance,
  result,
}: {
  instance: Instance;
  result: Result | null;
}) {
  const points =
    instance.geometry.kind === "coordinates"
      ? instance.city_ids.map((id) =>
          instance.geometry.kind === "coordinates"
            ? instance.geometry.points.find((p) => p.city_id === id)!
            : { x: 0, y: 0 },
        )
      : instance.city_ids.map((_, i) => ({
          x: Math.cos(
            (i * 2 * Math.PI) / instance.city_ids.length - Math.PI / 2,
          ),
          y: Math.sin(
            (i * 2 * Math.PI) / instance.city_ids.length - Math.PI / 2,
          ),
        }));
  const xs = points.map((p) => p.x),
    ys = points.map((p) => p.y);
  const mapped = points.map((p) => ({
    x:
      50 +
      ((p.x - Math.min(...xs)) / (Math.max(...xs) - Math.min(...xs) || 1)) *
        260,
    y:
      50 +
      ((p.y - Math.min(...ys)) / (Math.max(...ys) - Math.min(...ys) || 1)) *
        220,
  }));
  const tour = result?.assignment?.tour;
  return (
    <figure>
      <svg
        viewBox="0 0 360 320"
        role="img"
        aria-label={
          tour
            ? `Verified tour ${tour.join(" to ")}`
            : "City sketch, no solution selected"
        }
      >
        {tour && (
          <polyline
            points={tour
              .map((id) => mapped[instance.city_ids.indexOf(id)])
              .filter(Boolean)
              .map((p) => `${p.x},${p.y}`)
              .join(" ")}
            fill="none"
            stroke="#00877a"
            strokeWidth="3"
          />
        )}
        {mapped.map((p, i) => (
          <g key={instance.city_ids[i]}>
            <circle
              cx={p.x}
              cy={p.y}
              r="17"
              fill={
                instance.city_ids[i] === instance.depot_id
                  ? "#143c45"
                  : "#e4efec"
              }
              stroke="#143c45"
            />
            <text
              x={p.x}
              y={p.y + 5}
              textAnchor="middle"
              fill={
                instance.city_ids[i] === instance.depot_id ? "white" : "#143c45"
              }
            >
              {instance.city_ids[i]}
            </text>
          </g>
        ))}
      </svg>
      <figcaption>
        {instance.geometry.kind === "matrix"
          ? "Schematic city positions; distances come only from the supplied matrix."
          : "Planar coordinate sketch; Euclidean costs, not roads."}
      </figcaption>
    </figure>
  );
}

export function Results({ result }: { result: Result }) {
  const q = result.quantum;
  return (
    <section aria-label="Solve result" className="result">
      <p className="eyebrow">
        {result.method === "classical"
          ? "Classical result"
          : "Local quantum simulation · runs on a classical computer"}
      </p>
      <h2>
        {result.outcome === "no_feasible_sample"
          ? "No feasible sample"
          : result.assignment
            ? "Verified feasible tour"
            : "No verified solution"}
      </h2>
      <p role="status">
        Execution: <strong>{result.execution_status}</strong>
      </p>
      {result.assignment && (
        <p className="route">{result.assignment.tour.join(" → ")}</p>
      )}
      <dl className="metrics">
        <div>
          <dt>
            {q
              ? "Best feasible original cost across entire trace"
              : "Original tour cost"}
          </dt>
          <dd>
            {result.objective ?? "Unavailable"}{" "}
            <small>{result.objective_unit}</small>
          </dd>
        </div>
        <div>
          <dt>Total elapsed work (including cleanup)</dt>
          <dd>
            {result.total_elapsed_s.toFixed(4)} <small>seconds</small>
          </dd>
        </div>
        <div>
          <dt>Original constraints</dt>
          <dd>
            {result.validation.feasible === true
              ? "Verified feasible"
              : result.validation.feasible === false
                ? "Invalid"
                : "No candidate to validate"}
          </dd>
        </div>
        <div>
          <dt>Solver</dt>
          <dd>{result.solver_id}</dd>
        </div>
      </dl>
      {q && (
        <>
          <p className="notice">
            The displayed route is the best verified feasible sample across the
            entire optimization trace. It is not a claim about sampling at final
            optimizer parameters.
          </p>
          <dl className="metrics">
            <div>
              <dt>Total shots across optimizer evaluations</dt>
              <dd>
                {q.raw_shots} <small>in {q.evaluations} evaluations</small>
              </dd>
            </div>
            <div>
              <dt>Feasible / invalid shots</dt>
              <dd>
                {q.feasible_shots} / {q.invalid_shots}
              </dd>
            </div>
            <div>
              <dt>Feasible / invalid fractions</dt>
              <dd>
                {percent(q.feasible_fraction)} / {percent(q.invalid_fraction)}
              </dd>
            </div>
            <div>
              <dt>Optimizer success / convergence flag</dt>
              <dd>
                {q.optimizer_success === null
                  ? "Unavailable"
                  : String(q.optimizer_success)}
              </dd>
            </div>
            <div>
              <dt>Verified exact reference</dt>
              <dd>{q.exact_reference}</dd>
            </div>
            <div>
              <dt>Absolute gap against exact reference</dt>
              <dd>{q.absolute_gap ?? "Unavailable — no feasible sample"}</dd>
            </div>
          </dl>
          <p>Optimizer termination: {q.optimizer_message ?? "Unavailable"}</p>
        </>
      )}
      {!q && (
        <p>
          {result.proven_optimal
            ? "Optimality established by exact enumeration."
            : "OR-Tools is a heuristic baseline; original cost was independently recomputed."}
        </p>
      )}
      <p className="muted">
        Worker exit: {String(result.worker.worker_exitcode)} · Forced cleanup:{" "}
        {String(result.worker.forced_cleanup)}. RSS monitoring uses polling; no
        absolute hard memory guarantee.
      </p>
    </section>
  );
}

export function App() {
  const [input, setInput] = useState(JSON.stringify(preset, null, 2));
  const [method, setMethod] = useState("ortools_tsp");
  const [shots, setShots] = useState(256),
    [evaluations, setEvaluations] = useState(16),
    [seed, setSeed] = useState(1729),
    [timeout, setTimeoutValue] = useState(20);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [result, setResult] = useState<Result | null>(null),
    [solvedInstance, setSolvedInstance] = useState<Instance>(preset);
  const controller = useRef<AbortController | null>(null);
  const quantum = method === "quantum_local";
  const ref = uniformReference(
    result?.quantum?.raw_shots ?? shots * evaluations,
  );
  function changeInput(value: string) {
    setInput(value);
    setResult(null);
    setError("");
  }
  async function solve(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    let instance: Instance;
    try {
      instance = JSON.parse(input);
    } catch {
      setError("Invalid JSON. Enter a valid instance.");
      return;
    }
    setBusy(true);
    controller.current = new AbortController();
    const request: SolveRequest = {
      instance,
      method: quantum ? "quantum_local" : "classical",
      solver: method === "exact_tsp" ? "exact_tsp" : "ortools_tsp",
      timeout_s: timeout,
      memory_limit_mb: 512,
      scale: 1000,
      quantum: {
        shots,
        max_evaluations: evaluations,
        seed,
        backend: "statevector",
        transpiler_seed: 7,
        reps: 1,
        optimization_level: 1,
        timeout_s: timeout,
        memory_limit_mb: 512,
      },
    };
    try {
      const response = await fetch("/api/problems/tsp/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.current.signal,
      });
      const data = await response.json();
      if (!response.ok || !("execution_status" in data))
        throw new Error(
          data.error
            ? `${data.error.code}: ${data.error.message}`
            : "Request failed",
        );
      setResult(data as Result);
      setSolvedInstance(instance);
    } catch (e) {
      setError(
        e instanceof Error && e.name === "AbortError"
          ? "Request cancelled. The server is cleaning up its worker; new work may briefly return busy."
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
        <p className="eyebrow">QUANTUM WORKLOAD STUDIO / LOCAL TSP</p>
        <h1>
          A small tour.
          <br />
          An inspectable answer.
        </h1>
        <p className="intro">
          Explore one symmetric travelling salesperson problem, verify the
          route, and inspect what local simulation actually sampled.
        </p>
        <p className="disclaimer">
          Research prototype · No practical quantum speedup demonstrated ·
          Novelty unverified
        </p>
      </header>
      <div className="workspace">
        <section className="editor">
          <h2>1. Define the instance</h2>
          <p>
            One closed tour on supplied costs. Synthetic data and planar
            sketches are not delivery routing or road travel times.
          </p>
          <div className="buttons">
            <button
              type="button"
              disabled={busy}
              onClick={() => changeInput(JSON.stringify(preset, null, 2))}
            >
              Four-city matrix preset
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                changeInput(
                  JSON.stringify(
                    {
                      ...preset,
                      instance_id: "four_city_planar",
                      distance_unit: "planar_units",
                      geometry: {
                        kind: "coordinates",
                        metric: "euclidean_2d",
                        points: [
                          { city_id: "A", x: 0, y: 0 },
                          { city_id: "B", x: 1, y: 0 },
                          { city_id: "C", x: 1, y: 1 },
                          { city_id: "D", x: 0, y: 1 },
                        ],
                      },
                    },
                    null,
                    2,
                  ),
                )
              }
            >
              Planar coordinate example
            </button>
          </div>
          <label htmlFor="instance">
            Instance JSON — manually edit coordinates or symmetric matrix
          </label>
          <textarea
            id="instance"
            spellCheck={false}
            value={input}
            onChange={(e) => changeInput(e.target.value)}
            disabled={busy}
          />
          <form onSubmit={solve}>
            <h2>2. Choose a method</h2>
            <label htmlFor="method">Solver method</label>
            <select
              id="method"
              value={method}
              onChange={(e) => {
                setMethod(e.target.value);
                setResult(null);
              }}
              disabled={busy}
            >
              <option value="ortools_tsp">Classical · OR-Tools</option>
              <option value="exact_tsp">
                Classical · exact small-instance oracle
              </option>
              <option value="quantum_local">
                Opt in · local QAOA simulation
              </option>
            </select>
            {quantum && (
              <div className="notice">
                <p>
                  Opt-in local simulation runs classically. It can return no
                  feasible sample. Requires a separately installed quantum
                  environment and server opt-in. The API caps the requested
                  trace at 8,192 total shots.
                </p>
                <div className="fields">
                  <label>
                    Shots per evaluation
                    <input
                      type="number"
                      min="1"
                      max="4096"
                      value={shots}
                      onChange={(e) => setShots(+e.target.value)}
                      disabled={busy}
                    />
                  </label>
                  <label>
                    Optimizer evaluations
                    <input
                      type="number"
                      min="4"
                      max="50"
                      value={evaluations}
                      onChange={(e) => setEvaluations(+e.target.value)}
                      disabled={busy}
                    />
                  </label>
                  <label>
                    Sampling seed
                    <input
                      type="number"
                      min="0"
                      max="2147483647"
                      value={seed}
                      onChange={(e) => setSeed(+e.target.value)}
                      disabled={busy}
                    />
                  </label>
                </div>
              </div>
            )}
            <label>
              Whole-work deadline (seconds)
              <input
                type="number"
                min="0.001"
                max="60"
                step="0.001"
                value={timeout}
                onChange={(e) => setTimeoutValue(+e.target.value)}
                disabled={busy}
              />
            </label>
            <div className="buttons">
              <button className="primary" disabled={busy} type="submit">
                {busy ? "Solving…" : "Solve and verify"}
              </button>
              {busy && (
                <button
                  type="button"
                  onClick={() => controller.current?.abort()}
                >
                  Cancel request
                </button>
              )}
            </div>
          </form>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>
        <section className="answer">
          <h2>3. Inspect the result</h2>
          <Tour instance={solvedInstance} result={result} />
          {result ? (
            <Results result={result} />
          ) : (
            <p className="empty">
              Run a solver to see an independently validated route and measured
              result. No solution is prefilled.
            </p>
          )}
          <aside>
            <p className="eyebrow">
              ANALYTICAL SANITY REFERENCE · SUPPLIED MATRIX ONLY
            </p>
            <h3>Uniform random nine-bit sampling</h3>
            <p>
              Of 512 equally likely assignments, six are feasible (1.171875%)
              and two attain cost 4 (0.390625%). With{" "}
              {result?.quantum?.raw_shots ?? shots * evaluations} independent
              draws, the expected feasible count is{" "}
              {ref.expectedFeasible.toFixed(3)} and the expected optimal count
              is {ref.expectedOptimal.toFixed(3)}.
            </p>
            <p>
              This is an analytical sampling calculation for the supplied
              preset, not an executed random run, a quantum benchmark, or a
              claim about other instances. It excludes optimization and compute
              costs.
            </p>
          </aside>
        </section>
      </div>
      <footer>
        Checkpoint 1C · Symmetric TSP only · Unlicensed and unpublished pending
        owner decision. No cloud hardware or external routing services.
      </footer>
    </main>
  );
}
