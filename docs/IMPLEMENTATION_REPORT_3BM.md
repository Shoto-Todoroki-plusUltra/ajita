# Phase 3B-M mapping-only implementation — 25 October 2026

Owner scope: mapping implementation and mathematical tests only. No sampler,
QAOA optimizer, smoke attempt, study batch, QPU job or paid service was executed.
This report supplements, and does not replace, the historical implementation report.
AI-assisted implementation and documentation: OpenAI Codex; independent owner
review remains required. No novelty, quantum advantage or general scheduling claim.

## Baselines and changes

Accepted Phase 2 baseline: `c6afdcc00cbae93a6abdb3c35204403bf9635d3e`.
The already owner-accepted Phase 3A documents were committed unchanged as
`b14278e`. Tested mapping source milestone: `c7a8e40`.

- `execution/research_mapping.py`: explicit versioned TSP/B1 requests, canonical
  artifact hashes, original-instance hashes, independent canonical recompilation,
  at most nine active variables, and computed `none`/`ising_l1` normalization.
  Unknown versions, stale/mutated encodings and unsupported sizes are rejected.
  Hashes establish integrity, not a signature or authorization to execute.
- `qubo/basis.py`: reuse the existing quadratic coefficient expansion for the
  concrete B1 artifact type. The original domain encoders are unchanged.
  `Mapping.sparse_operator()` imports Qiskit only when explicitly called, returns
  nonidentity `SparsePauliOp` terms and a separate identity offset.
- `execution/local.py`: internal optional TSP research payload; parent and worker
  revalidate it. The default payload, penalty and operator remain unchanged.
  The explicit normalized path evolves with H/L and optimizes sampled E/L;
  original-domain candidate costs remain unscaled. No public API exposes this input.
  Algebra and admission are tested; execution of this new branch is deferred.
- B1 has only preflight and supplied-readout validation boundaries, not a quantum
  solver or worker entry point. Readout fixtures are synthetic unit-test inputs,
  expressly not measured shots. Malformed/infeasible readouts stay invalid;
  empty/no-feasible inputs have no fabricated best solution.
- Six minimal fixtures, fixed mathematical certificate script and mapping tests
  implement the frozen cases. This is not a benchmark runner or study dataset.
  The hook adds lint/format checks, not experimental execution.

Classical-only imports were checked in fresh subprocesses without quantum SDKs;
classical API/CLI remain usable in `.venv-api`. Public API, UI, old test files,
locks and historical evidence were not changed. `evidence/3bm/preservation.json`
checks 249 files against the accepted baselines, including all tracked historical
evidence and the unchanged Phase 3A protocol. Two pre-existing untracked root
files, `ajita.zip` and `ARCHIVE_MANIFEST.json`, were left untouched and excluded.

## Mathematical evidence

`evidence/3bm/mapping-certificate.json` contains the complete coefficient,
mapping, original-domain reference, validation and energy rows, source hashes,
lock/protocol hashes, package versions and actual worker lifecycle observations.
Absolute tolerance is 1e-10; relative tolerance 1e-12; imaginary residual tolerance
1e-10. No tolerance permits a change of original feasibility or objective.

| Case | Active bits | Feasible assignments | Exact original optimum | Penalties checked |
|---|---:|---:|---:|---|
| T0 | 9 | 6 | 4 (2 optima) | 4, 16, 64 |
| T1 | 9 | 6 | 10 (2 optima) | 14, 56, 224 |
| B0 | 4 | 2 | 1 | 1, 6, 24 |
| B1 | 8 | 8 | 1 | 2, 10, 40 |
| N0 | 2 | 0 | none: infeasible | 1, 4 |
| N1 | 0 | 0 | none: infeasible | 1 |

All 3,897 rows across 15 case/policy combinations were checked against the
separate direct constraint expression, expanded QUBO and classical Ising energy;
3,896 nonzero-qubit rows additionally have SDK basis expectations, both raw and
normalized. N1 has one empty assignment and a constant-only energy, not a claimed
zero-qubit SDK execution. TSP references enumerate original routes; B1 references
use original-domain enumeration/validation and separately check native CP-SAT.
The complete feasible objective multisets match decoded bitspace enumeration.
The certificate's maximum unnormalized SDK error is 0.0; maximum normalized
residual is 6.661338147750939e-16. Residuals are retained in every row.

Penalty sufficiency is separate from operator parity: B0 at penalty 1 has an
infeasible ground-state tie. N0/N1 are infeasible negative controls, never successful
solutions. No frozen fixture, penalty, seed or budget was changed and no protocol
discrepancy was found. These exact tiny facts are not sampling study findings.

Additional tests cover the accepted B1 tiny/tie/shared-conflict/capacity examples
with scales 0.25, 1 and 7, identity constants, signs, x=(1-Z)/2, normalization,
non-palindromic ordering, and a reversed physical layout with nonidentity classical
wiring. The latter uses deterministic X-only state preparation and basis algebra,
not a sampler. Logical i maps to qubit i and Pauli label character n-1-i; decoding
uses actual classical wiring and does not apply the physical permutation twice.

Official API references consulted: [SparsePauliOp](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.SparsePauliOp),
[Statevector](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Statevector),
and [bit ordering](https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering).

## Actual verification

Environment: native arm64 macOS 26.5.2, build 25F84; Python 3.12.13;
Qiskit 2.5.2, Aer 0.17.2, NumPy 2.5.4, SciPy 1.18.0, OR-Tools 9.15.6755,
Pydantic 2.14.1, psutil 7.2.2, pytest 9.1.1, Ruff 0.17.1;
Node 24.22.0. Existing pinned classical/optional-quantum installs were reused;
no dependency was installed or lock changed. Full detail: `environment.json`.

| Check | Actual outcome |
|---|---|
| Final optional-quantum mapping-only regression selection | 5,107 passed; 6 deselected; 0 failed; 0 skipped; 4 warnings; 28.38 s |
| Classical environment regression selection | 650 passed; 1 deselected; 0 failed; 0 skipped; 4 warnings; 21.11 s |
| Standalone bounded certificate | completed; 3,897 rows; zero sampler calls; exit 0; no forced cleanup; no surviving worker |
| Quality hook: Ruff, OpenAPI/TypeScript parity, frontend format | passed |
| Optional-quantum `pip check` | passed |
| Preservation audit | 249/249 unchanged |

The final quantum selection includes 1,180 existing tests and 3,927 new mapping
tests. This is **not** a full sampler-inclusive regression run. The safety plugin
explicitly deselects six existing sampler/QAOA tests; the classical selection's
one deselection is a subset of these. Exact node IDs are in `final-policy.json`.
It also rejects StatevectorSampler/Aer sampler calls and default QAOA worker
invocation; no forbidden attempts occurred. The standalone certificate adds
child-process sampler/worker denial. The normal test suite itself is unchanged.
No UI/browser flow was run because no UI changed and its quantum flow is outside
this authorization. Existing lifecycle, timeout, cancellation and resource tests
with nonquantum targets ran in the permitted selection.

The first new-test run had 3,923 passes and three failures: a hand-written test
expected B0's Ising identity constant to be 14.5 instead of 12 before scaling.
The independent expansion is 12 - 18/2 + 36/4 = 12. Only that test expectation
was corrected; direct/expanded/SDK parity already agreed. Initial failure XML/log
are retained. An intermediate full run had 5,107 passes/6 deselections in 33.41 s.
Warnings are the existing Starlette/httpx deprecation and three SWIG warnings.
Initial Ruff checks also found formatting/import issues; corrected before final
passing checks. Commands and authentic logs/XML are in `evidence/3bm/`.
`pip check` warned that the user cache was not writable and disabled its cache;
it reported no broken requirements. This was a read-only check, not an install.

The final standalone certificate measured 11.104049 s inside its calculation,
12.717151 s supervisor time including cleanup, 0.243351 s cleanup, and sampled
peak worker RSS 146,653,184 bytes. These are test-process observations, not QAOA
timings, performance claims or end-to-end HTTP/browser measurements. The existing
supervisor enforces a 60 s certificate deadline (within the 120 s mathematical
budget) and a sampled 512 MiB RSS guard. Sampling cannot guarantee a hard memory
ceiling or instantaneous termination. Future research preflight retains the
frozen p=1, 256-shot, 16-call, 20 s, 512 MiB caps; it performs no execution.

## Review package and remaining gate

`evidence/3bm/commands.md` records commands; `inventory.json` lists changed paths;
`evidence-hashes.json` covers the new evidence files except itself. The committed
source is packaged by the existing archive script from Git HEAD with the required
`.gitignore`, `.github/workflows/checks.yml` and `.githooks/pre-commit`.
Its external manifest hashes the actual archive members (including the embedded
manifest); its verifier checks member hashes, required hidden files and CRC.
Environments, Git internals, credentials, caches and untracked files are excluded.
Archive and whole-ZIP SHA-256 are returned separately after this report's commit
to avoid a self-referential hash. Old raw artifacts remain included unchanged.

Outstanding: the historical 20–30 s OR-Tools cold-start/tail-latency risk remains
unresolved; no root-cause fix is claimed. Real research sampling, new normalized
worker execution, full sampler regressions and B1 smoke execution are untested
under this authorization. Mathematical parity does not establish useful QAOA
sampling, optimizer convergence, speedup or novelty. Only this Mac was tested.
Zero-active-variable N1 remains a classical constant-only control. Classical
cleanup protections remain sampled/best effort, not absolute OS guarantees.

Stop here for independent 3B-M mapping acceptance. The optional B0/B1 sampler
smokes require separate express owner approval. Neither 3B-E nor 3C-R, cloud,
public push, publication or license action is authorized by this work.
