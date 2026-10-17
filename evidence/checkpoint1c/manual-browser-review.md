# Manual Mac browser review — 16 October 2026

Codex used the desktop's in-app browser, through accessibility/DOM controls, at `http://127.0.0.1:5173`. This was a real Vite/React page calling the real loopback FastAPI server in `.venv-api-quantum`, not a mocked UI. This review supplements automated Chromium; it is not Safari/Firefox certification or independent human review.

1. Opened the page, checked that no solution was prefilled and that synthetic-cost, simulator and uniform-reference qualifications were visible.
2. Selected the default OR-Tools flow and clicked Solve. The initial run returned a visible `timeout: Local worker did not finish cleanly` at the supplied 20-second deadline. An early three-second browser wait also expired; no success was inferred from the click.
3. Later repeated real requests succeeded. The manual OR-Tools page displayed A → D → C → B → A, original cost 4, verified feasible, measured elapsed 0.7744 seconds, worker exit 0 and forced cleanup false.
4. Selected opt-in local QAOA through the actual method control and clicked Solve. The page displayed execution completed, A → D → C → B → A, trace-best original cost 4, 4,096 shots in 16 evaluations, 61 feasible / 4,035 invalid, fractions 1.4893% / 98.5107%, exact reference 4, gap 0, optimizer success false/MAXFUN and elapsed 1.3654 seconds. The final-parameter disclaimer and analytical uniform calculation were visible.
5. Reviewed the separately saved automated desktop/mobile screenshots for readability, labels, route and no horizontal overflow. The screenshot timing is from its own actual automated run, not the manual run above.
6. Closed the temporary manual-test tab and shut down the two manual-test servers. No user tab was modified. No source fixture supplied these results.

Intermittent initial delays remain a reported limitation. A later standalone OR-Tools import took ~0.172 seconds and three API probes took ~0.18–0.46 seconds wall time. These observations do not establish the cause of the initial delays, nor justify promising a cold-start time.
