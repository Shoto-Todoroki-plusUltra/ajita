# Local demo

Start with the classical solvers. The examples run locally and do not need an IBM account or any external API.

## Setup

Use Python 3.12 on a native Apple Silicon Mac, with Node **24.22.0** and npm **11.19.1**. The dependency locks were tested on that platform.

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api
.venv-api/bin/python -m pip install --require-hashes -r requirements/api-macos-arm64-py312.lock
.venv-api/bin/python -m pip install --no-deps --no-build-isolation -e .
node --version
npm --version
npm ci --prefix frontend
```

Start the API in one terminal:

```sh
QWS_ENABLE_LOCAL_QUANTUM=0 PYTHONPATH=src .venv-api/bin/python -m uvicorn quantum_workload_studio.api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

Start the UI in another:

```sh
npm --prefix frontend run dev
```

Open **http://127.0.0.1:5173**. API documentation is available at **http://127.0.0.1:8000/docs**. Keep the service on loopback with one worker. Stop each process with Control-C.

## Try the examples

1. Keep the four-city matrix preset. Select the exact small-instance oracle and click **Solve and verify**. The optimum is **4**. Switch to OR-Tools to compare a heuristic route with the exact reference. Matrix drawing positions are schematic; the matrix supplies the costs.
2. Edit the matrix or load the planar coordinate example. Previous results clear when the input changes. The uniform nine-bit reference is analytical and appears only for the unchanged original preset.
3. Switch to **Classroom timetable**. Solve the two-course preset with CP-SAT. Its original preference objective and bound are **1**, with OPTIMAL status. The exhaustive solver provides a tiny-instance reference.
4. Compile the B1 QUBO and inspect `1010`: both courses occupy the same slot and violate the resource constraints. Inspect `1001`: Math/S1 and Physics/S2 form a valid assignment of cost **1**. B1 inspection strings use index order, with variable zero on the left.

Backend elapsed time includes worker cleanup but excludes HTTP and browser latency. A good objective, a feasibility check and an optimality proof are different pieces of information.

## CLI examples

```sh
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli solve --instance examples/tsp/four_city.json --solver exact_tsp
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli solve --instance examples/tsp/four_city.json --solver ortools_tsp --scale 1000 --timeout-s 1
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver cp_sat
PYTHONPATH=src .venv-api/bin/python -m quantum_workload_studio.cli timetable solve --instance examples/timetable/tiny.json --solver enumeration
```

## Optional TSP simulation

The quantum environment is separate from the classical install:

```sh
/opt/homebrew/bin/python3.12 -m venv .venv-api-quantum
.venv-api-quantum/bin/python -m pip install --require-hashes -r requirements/api-quantum-macos-arm64-py312.lock
.venv-api-quantum/bin/python -m pip install --no-deps --no-build-isolation -e .
```

Stop the classical API, then start the same service with `QWS_ENABLE_LOCAL_QUANTUM=1` and `.venv-api-quantum/bin/python`. Select local quantum in the TSP UI. This executes a bounded CPU simulation and may return no feasible sample. Read execution status, invalid-shot counts and optimizer status alongside the best original cost. See [verification](VERIFICATION.md) for recorded results and limits. Timetabling does not offer quantum execution.

## Screenshots and recording

If a live setup is unavailable, use the two screenshots in the README and explicitly describe them as recorded results. Do not present a screenshot as a fresh solve.

For a short Mac recording, use **Shift-Command-5 → Record Selected Portion** and frame the browser content. In 60–90 seconds, show a TSP solve, the timetable grid and an invalid candidate inspection, then mention the simulator and problem-size limits. Review the recording for personal information before sharing. No video is included in this repository.
