# Phase 3A primary-source review

24 October 2026. **Research/design only.** Phase 2 was accepted by the owner with recorded limitations. This review does not authorize implementation or experiments. Accepted source baseline: `c6afdcc00cbae93a6abdb3c35204403bf9635d3e`. Earlier source, evidence, locks and historical reports are unchanged. No publication, novelty, quantum acceleration or independent reproduction of these papers is claimed.

## Finding and search boundary

The broad question “do penalties affect feasibility, original solution quality and resources?” already has substantial answers. Static permutation penalties, QAOA penalty/quality trade-offs, constraint-preserving mixers, school scheduling QAOA, railway formulation comparisons and fair benchmarking all predate Ajita. A different application wrapper or combination of two domains does not establish a scientific gap. The defensible next step is a **small bounded replication/characterization**, not a new penalty-selection algorithm.

Targeted primary-source searches covered permutation/TSP penalties; school/classroom and railway scheduling QUBOs; constrained QAOA and feasibility-preserving operators; application-level benchmarking. Sources below are author/institutional manuscripts, original proceedings, publisher records or official SDK documentation. Search-engine summaries and ResearchGate were discovery leads only. Selected methods, numerical sections, tables and conclusions were read where accessible; this is not a systematic review, exhaustive search or reproduction. Source access date is 24 October 2026; explicit arXiv versions distinguish inspected text from evolving pages.

## Evidence ledger

### P1 — permutation penalty selection is established

Mayowa Ayodele (2022), **Penalty Weights in QUBO Formulations: Permutation Problems**, EvoCOP; [DOI 10.1007/978-3-031-04148-8_11](https://doi.org/10.1007/978-3-031-04148-8_11), [author text, arXiv:2206.11040v1](https://arxiv.org/html/2206.11040v1). Inspected §§2–7, especially §§3, 5–6/Tables 1–8.

- **Methods/resources:** two-way one-hot TSP/QAP; UB, maximum-coefficient, Verma–Lewis and proposed static penalty policies. CPU implementation of Digital Annealer-style search and Fujitsu DA3 special-purpose classical CMOS hardware, **not QAOA or a QPU**. TSPLIB/QAPLIB, 20 independent repetitions; CPU iteration limits versus DA3 time limits.
- **Metrics/findings:** average relative percentage deviation from known references and penalty validity; demonstrates too-small weights can fail feasibility and larger conservative weights need not yield better heuristic search. Some DA3 differences are small; no universal optimum weight follows.
- **Ajita difference:** finite-shot X-mixer QAOA and tiny B1 are different dynamics. This paper already addresses static penalty policy comparison; its general findings cannot be presented as ours. Exact CPU model details were not transcribed into this review, and no timing result is transferred.

### P2 — direct TSP variational evidence, including negative findings

Lilly Palackal, Benedikt Poggel, Matthias Wulff, Hans Ehm, Jeanette Miriam Lorenz and Christian B. Mendl (2023), **Quantum-Assisted Solution Paths for the Capacitated Vehicle Routing Problem**, IEEE QCE; [DOI 10.1109/QCE57702.2023.00080](https://doi.org/10.1109/QCE57702.2023.00080), [institutional author manuscript](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/3c1de489-32f7-45b7-ba35-332c11991fa6/content), [arXiv:2304.09629v2](https://arxiv.org/abs/2304.09629v2). Inspected TSP formulation, §§III-C/IV, Tables I–III.

- **Methods/resources:** 4–6-city, depot-fixed TSPs with 9/16/25 qubits; IBM statevector simulation, QAOA p=5, optimizer/scaling/initialization/penalty studies, and VQE. Its hardware-marked results concern VQE; its poor QAOA simulations did not justify a QAOA hardware run. Exact hardware backend identity was not established here; do not guess it.
- **Metrics/findings:** shot feasibility and feasible-tour length relative to optimum, separately from Ising energy. QAOA often gave poor feasible amplification; penalty experiments also include VQE and must not be mislabeled QAOA results. This already studies much of the proposed TSP question.
- **Ajita difference:** p=1, tightly capped finite shots/evaluations, smaller locked fixtures. Only its TSP methods inform this review; its CVRP decomposition does not authorize CVRP work.

### P3 — permutation penalties, feasibility and TSP comparisons overlap directly

Ge Yan, Mengfei Ran, Ruocheng Wang, Kaiseng Pan and Junchi Yan (2024), **Rethinking Parity Check Enhanced Symmetry-Preserving Ansatz**, NeurIPS 37; [original proceedings/DOI 10.52202/079017-2076](https://proceedings.neurips.cc/paper_files/paper/2024/hash/7798f18a1e91aff7ad1df4841d6a01a8-Abstract-Conference.html), [paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/7798f18a1e91aff7ad1df4841d6a01a8-Paper-Conference.pdf). Inspected §3.3–3.4, Appendix F.1–F.3, Figures 5–6/Table 9.

- **Methods/resources:** Hamming-weight-preserving ansätze/parity checks versus soft-penalty HEA, QAOA and XY mixers; QAP and simulated TSP. Penalty sensitivity spans different weights. TSP includes 100 random instances per size 3–6; soft-constraint simulations are more limited. Separate QAP hardware experiment uses 12 selected qubits of a 66-qubit superconducting processor; this is not a TSP hardware result.
- **Metrics/findings:** feasible probability, feasible/all-state normalized quality and optimum probability. Reports a trade-off between low-penalty feasible quality and feasibility; large penalties can yield essentially random feasible quality. Hardware topology and circuit costs are explicit concerns.
- **Ajita difference:** no parity checks, custom hard mixer, postselection objective or hardware. A simpler repeat with different caps is a replication, not discovery of penalty sensitivity.

### P4 — classroom/school quantum timetabling predates Ajita

Otto Menegasso Pires (2021), **A quantum heuristic for the school timetabling problem**, Master's dissertation, Universidade Federal de Santa Catarina; [institutional record](https://repositorio.ufsc.br/handle/123456789/231060), [full thesis](https://repositorio.ufsc.br/bitstream/handle/123456789/231060/PGCC1209-D.pdf?isAllowed=y&sequence=-1). Inspected scope, results and conclusion (printed pp.16, 33–39). The thesis identifies related Pires–Santiago–Marchi CEC 2021 work; that conference paper was not independently full-text reviewed.

- **Methods/resources:** two-stage graph-coloring/QAOA hard constraints followed by classical soft-objective optimization; Denmark-Smallschool and two derived XHSTT instances. Ket Parallel Bitwise Simulator, noiseless, up to 189 logical qubits; not a dense 189-qubit statevector or QPU execution.
- **Metrics/findings:** expected soft objective and objective distributions versus initial state/depth. The original instance could not improve because mixer reachability was restrictive; Den-Aux also failed to improve, while relaxed Den-5 improved at p=2.
- **Ajita difference:** B1 assigns rooms/capacities and single-slot events with an X mixer; it has no periodic school model or equivalent simulator. Negative mixer results are relevant precedent, not a promise of feasibility from custom mixers.

### P5 — railway reformulation already links quality and resources

Camille Grange, Marion Lavignac, Valentina Pozzoli and Eric Bourreau (2024), **Quadratic versus Polynomial Unconstrained Binary Models for Quantum Optimization illustrated on Railway Timetabling**; [arXiv:2411.10062v1](https://arxiv.org/html/2411.10062v1). Inspected §§2–4, particularly §4.1/Table 3 and §4.2.

- **Methods/resources:** simplified railway planning/extended bin packing; PUBO binary-penalty versus QUBO with extra variables; p=1 QAOA, COBYLA, 10 shots per evaluation, 100 runs per instance, no optimizer-call cap. IBM classical 32-qubit `qasm_simulator`, not QPU. Three examples require QUBO 15/17/20 versus PUBO 7/9/11 qubits.
- **Metrics/findings:** returned original-problem optimal/feasible-nonoptimal/infeasible proportions, not merely penalized energy. PUBO performed better on those examples. Qubit-space size, auxiliaries and optimization landscape all change; this is not an isolated coefficient-only causal test.
- **Ajita difference:** B1 has no auxiliary variables, different objective/constraints, and a strict evaluation cap. Do not infer a general PUBO advantage, import its success percentages or implement PUBO as an unapproved expansion.

### P6 — constrained QAOA alternatives are established

Stuart Hadfield, Zhihui Wang, Bryan O'Gorman, Eleanor G. Rieffel, Davide Venturelli and Rupak Biswas (2019), **From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz**, Algorithms 12(2), 34; [DOI 10.3390/a12020034](https://doi.org/10.3390/a12020034), [author PDF, arXiv:1709.03489](https://arxiv.org/pdf/1709.03489). Inspected ansatz/design conditions and permutation/scheduling mappings; not every construction/proof independently verified.

- **Method/resources:** theory and circuit constructions for feasible-subspace initial states and mixing operators, with locality/implementation considerations. Not a hardware benchmark or an experimentally optimized penalty grid.
- **Metrics/result:** establishes a framework for maintaining constraints with suitable mixers; it does not guarantee that an arbitrary feasible mixer is connected or cheap, or that every scheduling constraint is automatically preserved.
- **Ajita difference:** the proposed study deliberately retains uniform initialization and transverse-X mixing, allowing invalid states. Adding a feasible mixer would change the algorithm, initialization, accessible space and resource question; it is excluded from this protocol.

Dylan Herman, Ruslan Shaydulin, Yue Sun, Shouvanik Chakrabarti, Shaohan Hu, Pierre Minssen, Arthur Rattew, Romina Yalovetzky and Marco Pistoia (2023), **Constrained optimization via quantum Zeno dynamics**, Communications Physics 6, 219; [DOI 10.1038/s42005-023-01331-9](https://doi.org/10.1038/s42005-023-01331-9), [author text, arXiv:2209.15024v6](https://arxiv.org/html/2209.15024v6). Inspected numerical/penalty-tuning and hardware sections.

- **Method/resources:** constrained portfolio QAOA simulations, penalty-factor sweeps and repeated constraint-checking measurements; separate four-asset p=1 proof-of-concept on Quantinuum H1-2, 2,000 shots, no error mitigation, parameters optimized noiselessly.
- **Metrics/findings:** original approximation quality and in-constraint probability; penalty dependence can be nonmonotonic and multi-constraint tuning costly. Hardware establishes the tested oracle/measurement mechanism, not general optimization advantage.
- **Ajita difference:** no mid-circuit constraint checks or portfolio model. These results already answer the general feasibility/penalty-trade-off question but cannot predict Ajita's small fixed-budget outcome.

### P7 — benchmarking principles and TSP formulation comparisons exist

David Bucher, Nico Kraus, Jonas Blenninger, Michael Lachner, Jonas Stein and Claudia Linnhoff-Popien (2024), **Towards Robust Benchmarking of Quantum Optimization Algorithms**; [arXiv:2405.07624v1](https://arxiv.org/html/2405.07624v1). Inspected §§III/IV-B, Table II/Figure 7 and comparison boundaries.

- **Methods/resources:** equal tuning effort, native classical formulations, fixed-runtime quality, TTS and feasibility. TSP simulations compare QUBO/HOBO, XY and permutation mixers up to six-city/25-qubit QUBO. Parameter training uses L-BFGS on separate training data. The TSP section is explicitly QAOA-only; other examples include D-Wave/classical algorithms.
- **Metrics/findings:** TSP original-quality/feasibility-aware error and TTS in **CNOT-layer units**; some permutation-mixer circuit costs remain unavailable. That proxy is not measured wall-clock QPU advantage. Different ansätze change feasible space and circuit complexity.
- **Ajita difference:** a few synthetic fixed instances, no training set, local CPU simulation, measured complete attempt time. This study is not representative of operational instances or classical hardness.

Nils Quetschlich, Lukas Burgholzer and Robert Wille (2023), **MQT Bench: Benchmarking Software and Design Automation Tools for Quantum Computing**, Quantum 7, 1062; [DOI 10.22331/q-2023-07-20-1062](https://doi.org/10.22331/q-2023-07-20-1062), [author manuscript](https://www.cda.cit.tum.de/files/eda/2023_quantum_mqt_bench.pdf). Publisher overview/manuscript introduction reviewed. Cross-level circuit benchmarking from algorithm through native/mapped circuits is prior art; the reported suite is not a routing-feasibility or solver-speedup certificate. Ajita can adopt level-separated resource reporting without claiming the idea is new. No MQT package installation or comparator execution occurred here.

### P8 — later educational QUBO/annealing claims warrant timing caution

Ziyu Zhou, Shuyan Li, Mengtong Tan, Chaojie Zhang and Qing Chen (2025), **Hybrid quantum annealing for large-scale exam scheduling: Validation in real-world educational scenarios**, Applied Soft Computing 184(A), 113756; [DOI 10.1016/j.asoc.2025.113756 / publisher abstract](https://www.sciencedirect.com/science/article/abs/pii/S1568494625010695). Abstract and accessible publisher excerpts only; full methods were not available in this review.

The authors report graph preprocessing, a QUBO/hybrid D-Wave Advantage path, 2,749 exam instances and zero conflicts, contrasting 86 ms QPU time with 13,547 ms CPU simulated-annealing time. These are **author-reported resource-specific timings**, not verified equal end-to-end costs; access overhead, classical hybrid work, tuning and stronger native baselines cannot be resolved from the abstract. No practical advantage claim is adopted. Exam/student data and hybrid annealing differ substantially from B1 and local QAOA. This source establishes additional educational overlap; it does not supply a reproducible penalty rule for Ajita.

## What is settled, what remains an empirical question

| Layer | Already established / covered by accepted Ajita evidence | What the prospective study can actually assess |
| --- | --- | --- |
| Ground-state correctness | One-hot penalties and Ising encodings are longstanding; sufficient bounds are mathematical statements. Ajita already has independent tiny original oracles and exhaustive QUBO tests. | Re-certify every **new fixture/weight/scale** before sampling; label below-bound weights empirically adequate/inadequate/tied, rather than assuming failure. |
| Sampling/quality | P2/P3/P6 already show that large penalties need not improve useful original-objective sampling; P4 documents constrained-mixer limitations. | A preregistered comparison of two sufficient weights under **this specific implementation/budget**, with weak penalties and impossible instances as diagnostics. No general transfer rule. |
| Compilation | P5/P7 show formulation and circuit resources matter. Coefficient changes do not inherently add interactions. | Whether term cancellations or actual compiler simplification change the frozen circuit; unchanged counts are informative and expected to be possible. |
| Cost/solver quality | P7 establishes native classical formulations, tuning effort and holistic timing requirements. | Local practical performance on tiny cases, including all overhead/failures; no inference to QPU runtime or hard industrial instances. |

The remaining uncertainty is configuration-specific and experimentally testable. It is **not evidence of an unstudied topic**. A null/negative replication is an admissible result; if a later search finds the exact protocol already run, position the work as reproducibility/engineering rather than inventing another gap.

## Read limits, source failures and reproducibility

HTML requests for arXiv `2405.07624v2` and `1709.03489v3` returned 404; the actual first paper has v1, and the second was read through its author PDF/publisher record. A direct MDPI request returned 429. PDF text search sometimes returned no match for partial words; that is not evidence that a method was absent. Publisher/author PDFs and selected explicit sections resolved key experimental details. P8 remains an abstract-level lead; recent academic timetabling/annealing leads with inaccessible detailed methods were not treated as validated comparisons. Verma–Lewis is discussed through P1, not represented as independently reproduced or fully reviewed here. No paper's marketing/advantage assertion is adopted.

Current official API checks were limited to the design boundary: [Qiskit QAOA ansatz](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.qaoa_ansatz), [StatevectorSampler V2](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.primitives.StatevectorSampler), [bit order](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering), [SciPy COBYLA](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html) and [OR-Tools CP-SAT status](https://developers.google.com/optimization/cp/cp_solver). No SDK update or compatibility run occurred. The existing locked releases, not “latest” docs, govern future reproduction until separately reviewed.

See [prospective protocol](PHASE3_EXPERIMENT_PROTOCOL.md) and [approval/decision gate](PHASE3_DECISION_GATE.md). No new application source, benchmark code, fixtures on disk, tests, measurements or dependencies were created in Phase 3A.
