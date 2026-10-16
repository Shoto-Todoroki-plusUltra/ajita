import signal
import threading
import time

import pytest

pytest.importorskip("qiskit")
psutil = pytest.importorskip("psutil")

from quantum_workload_studio.execution.local import LocalOptions, memory_preflight, run_local, summarize_samples, supervise


def _sleep_worker(send, payload):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    send.send({"kind": "started"})
    time.sleep(30)


def _memory_worker(send, payload):
    retained = bytearray(128*1024**2)
    send.send({"kind": "allocated", "bytes": len(retained)})
    time.sleep(30)


def _error_worker(send, payload):
    send.send({"kind":"error", "type":"RuntimeError", "message":"injected test failure, not backend output"})
    send.close()


def _invalid_sample_worker(send, payload):
    send.send({"kind":"samples", "raw_counts":{"bad":3}})
    time.sleep(30)


def test_validation_error_keeps_raw_event_and_cleans_up():
    def reject(event):
        raise ValueError("invalid readout in test")
    result = supervise({}, LocalOptions(timeout_s=5.0), target=_invalid_sample_worker, on_event=reject)
    assert result["execution_status"] == "validation_error"
    assert result["events"][0]["raw_counts"] == {"bad":3}
    assert result["events"][1]["phase"] == "parent_sample_validation"
    assert not result["worker_alive_after_cleanup"]


def test_worker_errors_are_not_success_or_fallback():
    result = supervise({}, LocalOptions(timeout_s=5.0), target=_error_worker)
    assert result["execution_status"] == "error"
    assert result["events"][0]["kind"] == "error"
    assert not result["worker_alive_after_cleanup"]


def test_guard_before_allocation():
    options = LocalOptions()
    for n in [25, 49, 0, True]:
        with pytest.raises(ValueError):
            memory_preflight(n, options, available_bytes=8*1024**3)
    with pytest.raises(ValueError, match="half"):
        memory_preflight(9, options, available_bytes=128*1024**2)
    with pytest.raises(ValueError, match="modeled"):
        memory_preflight(9, LocalOptions(memory_limit_mb=64), available_bytes=8*1024**3)
    report = memory_preflight(9, options, available_bytes=8*1024**3)
    assert report["amplitude_lower_bound_bytes"] == 8192


def test_counts_weighted_and_invalid(instance):
    result = summarize_samples(instance, {"100010001": 3, "000000000": 6, "bad": 1})
    assert result["raw_shots"] == 10
    assert result["feasible_shots"] == 3 and result["invalid_shots"] == 7
    assert result["feasible_fraction"] == 0.3
    assert result["best_feasible"]["original_objective"] == 4
    assert summarize_samples(instance, {"000000000": 5})["candidate_outcome"] == "no_feasible_sample"
    assert summarize_samples(instance, {})["feasible_fraction"] is None


def test_timeout_kills_uncooperative_worker():
    options = LocalOptions(timeout_s=0.5)
    start = time.monotonic()
    result = supervise({}, options, target=_sleep_worker)
    assert result["execution_status"] == "timeout"
    assert not result["worker_alive_after_cleanup"]
    assert not psutil.pid_exists(result["worker_pid"])
    assert time.monotonic()-start < 2


def test_cancel_kills_worker():
    cancel = threading.Event()
    timer = threading.Timer(0.5, cancel.set)
    timer.start()
    try:
        result = supervise({}, LocalOptions(timeout_s=5.0), target=_sleep_worker, cancel=cancel)
    finally:
        timer.cancel()
    assert result["execution_status"] == "cancelled"
    assert not result["worker_alive_after_cleanup"] and not psutil.pid_exists(result["worker_pid"])


def test_rss_monitor_enforces_sampled_limit():
    result = supervise({}, LocalOptions(timeout_s=5.0, memory_limit_mb=64), target=_memory_worker)
    assert result["execution_status"] == "memory_limit"
    assert result["observed_peak_worker_rss_bytes"] > 64*1024**2
    assert not result["worker_alive_after_cleanup"]


def test_actual_deadline_retains_honest_no_samples(instance):
    result = run_local(instance, LocalOptions(timeout_s=0.01))
    assert result["execution_status"] == "timeout"
    assert result["samples"]["raw_shots"] == 0
    assert result["samples"]["candidate_outcome"] == "no_feasible_sample"
    assert result["absolute_optimality_gap"] is None
    assert not result["worker_alive_after_cleanup"]


def test_real_qaoa_reproducible_and_bounded(instance):
    options = LocalOptions(max_evaluations=4, shots=32)
    first, second = run_local(instance, options), run_local(instance, options)
    assert first["execution_status"] == second["execution_status"] == "completed"
    assert first["samples"]["raw_counts"] == second["samples"]["raw_counts"]
    assert len(first["sample_evaluations"]) == 4
    assert first["samples"]["raw_shots"] == 128
    assert first["samples"]["feasible_shots"]+first["samples"]["invalid_shots"] == 128
    assert not first["worker_alive_after_cleanup"] and not first["failures"]
    for evaluation in first["sample_evaluations"]:
        assert evaluation["validation"]["raw_shots"] == 32
        assert len(evaluation["validation"]["decoded_unique_samples"]) == len(evaluation["raw_counts"])
    completed = next(e for e in first["events"] if e["kind"] == "completed")
    assert completed["optimizer"]["nfev"] == 4


def test_fail_closed_if_memory_monitor_unavailable(monkeypatch):
    def denied(self):
        raise psutil.AccessDenied(self.pid)
    monkeypatch.setattr(psutil.Process, "memory_info", denied)
    result = supervise({}, LocalOptions(timeout_s=5.0), target=_sleep_worker)
    assert result["execution_status"] == "monitor_unavailable"
    assert not result["worker_alive_after_cleanup"]


def test_local_cli_failure_artifacts(tmp_path, capsys):
    import json
    from pathlib import Path
    from quantum_workload_studio.local_cli import main
    fixture = Path(__file__).parents[2]/"examples/tsp/four_city.json"
    output = tmp_path/"timeout.json"
    assert main(["--instance",str(fixture),"--output",str(output),"--timeout-s","0.01"]) == 1
    result = json.loads(output.read_text())
    assert result["execution_status"] == "timeout" and result["samples"]["raw_shots"] == 0
    assert not result["worker_alive_after_cleanup"]
    assert main(["--instance",str(fixture),"--output",str(output),"--memory-mb","64"]) == 2
    assert json.loads(output.read_text())["execution_status"] == "preflight_error"
