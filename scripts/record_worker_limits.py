"""Save actual timeout/cancellation probes against the real local worker."""
import json
from pathlib import Path
import threading

from quantum_workload_studio.execution.local import LocalOptions, memory_preflight, run_local
from quantum_workload_studio.models.tsp import TspInstance


def main():
    instance = TspInstance.model_validate_json(Path("examples/tsp/four_city.json").read_text())
    timeout = run_local(instance, LocalOptions(timeout_s=0.01))
    cancel = threading.Event()
    timer = threading.Timer(0.02, cancel.set)
    timer.start()
    try:
        cancelled = run_local(instance, LocalOptions(), cancel=cancel)
    finally:
        timer.cancel()
    assert timeout["execution_status"] == "timeout"
    assert cancelled["execution_status"] == "cancelled"
    assert not timeout["worker_alive_after_cleanup"] and not cancelled["worker_alive_after_cleanup"]
    try:
        memory_preflight(25, LocalOptions())
        raise AssertionError("oversized preflight accepted")
    except ValueError as error:
        rejection = {"active_variables":25, "error":str(error), "worker_spawned":False}
    Path("evidence/checkpoint1b/worker-limits.json").write_text(json.dumps(
        {"timeout":timeout,"cancellation":cancelled,"oversized":rejection,
         "note":"Intentional lifecycle probes, not successful QAOA experiments."},indent=2)+'\n')
    print("Timeout, cancellation, no surviving worker, and oversized rejection verified")


if __name__ == "__main__":
    main()
