# Paste this into Codex

We're starting an open-source project called **Quantum Workload Studio**. Read `PROJECT_BRIEF.md` in the repository root **in full** before proposing changes. Treat its architecture, constraints, milestones, quality gates, correctness requirements, and honesty rules as binding until I explicitly revise them.

**First task: Phase 0 only — research and design, NOT coding the application yet.** Inspect the repository, review current official Qiskit, IBM Quantum Compute, Qiskit Optimization and Google OR-Tools documentation, check relevant prior art (particularly MQT and classical routing/scheduling systems), and prepare:

1. `docs/PRIOR_ART.md` — what already exists, sources/URLs, overlap, unsettled novelty.
2. `docs/ARCHITECTURE.md` — concrete directory layout, typed model schemas, solver and QUBO adapter boundaries, encoding/decoding and verification plan, target Mac environment.
3. `docs/DECISIONS.md` — design trade-offs, limitations, no-quantum-advantage assumption, and why initial TSP precedes vehicle routing.
4. `docs/PHASE_PLAN.md` — executable, small tasks with tests and phase acceptance criteria; stop after Phase 0.

Do not implement product source code or create paid cloud resources at this stage. Do not claim the project or its mechanisms are novel. Cite actual package documentation and identify any compatibility issues with my Mac. If crucial environment information is unavailable, list it explicitly rather than guessing. Summarize discoveries and ask for my approval before starting Phase 1.
