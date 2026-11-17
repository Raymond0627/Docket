"""Tests for background job execution + SSE subscription.

Root cause being fixed: the job used to run *inside* the SSE request, so a
client disconnect (tab switch, reload, closing the browser) killed the job
mid-way and left the row stuck at status='processing'.
"""
import json
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.api.jobs import db as jobs_db
from backend.models import JobStatus


@pytest.fixture
def client():
    return TestClient(app)


def _make_job(client, tmp_path, file_count=4) -> str:
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    for i in range(file_count):
        (src / f"note{i}.txt").write_text("ordinary notes about rent payment", encoding="utf-8")

    res = client.post("/api/jobs", json={
        "source_path": str(src),
        "output_path": str(out),
        "file_mode": "copy",
        "confidence_threshold": 80.0,
        "folder_template": "{owner}/{doc_type}/",
    })
    assert res.status_code == 200
    return res.json()["id"]


def _wait_for_status(client, job_id, statuses, timeout=20.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = client.get(f"/api/jobs/{job_id}").json()["status"]
        if status in statuses:
            return status
        time.sleep(0.1)
    raise AssertionError(
        f"job {job_id} never reached {sorted(statuses)}; "
        f"last status={client.get(f'/api/jobs/{job_id}').json()['status']}"
    )


def _read_stream(client, job_id) -> list:
    events = []
    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
        for line in stream.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


def test_job_completes_after_client_disconnects(client, tmp_path):
    """Closing the SSE stream must not abort the running job."""
    job_id = _make_job(client, tmp_path, file_count=6)

    # Connect, read only the first event, then disconnect immediately.
    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
        first = next(stream.iter_lines())
        assert first.startswith("data: ")

    # The job must keep running in the background and finish.
    status = _wait_for_status(client, job_id, {"completed", "failed"})
    assert status == "completed", "job should complete even with no SSE client attached"

    files = client.get(f"/api/jobs/{job_id}/files").json()
    assert len(files) == 6


def test_stream_after_completion_replays_without_reprocessing(client, tmp_path):
    """Re-opening the stream replays recorded events; it must not run the job again."""
    job_id = _make_job(client, tmp_path, file_count=3)

    first_events = _read_stream(client, job_id)
    assert first_events[-1]["event"] == "job_completed"
    rows_after_first = len(client.get(f"/api/jobs/{job_id}/files").json())
    assert rows_after_first == 3

    # Second subscriber sees the full event history...
    second_events = _read_stream(client, job_id)
    kinds = [e["event"] for e in second_events]
    assert kinds[0] == "job_started"
    assert kinds[-1] == "job_completed"
    assert kinds.count("file_processed") == 3

    # ...and the job was not re-processed (no duplicated job_files rows).
    rows_after_second = len(client.get(f"/api/jobs/{job_id}/files").json())
    assert rows_after_second == 3, "stream re-ran the job and duplicated results"


def test_stale_processing_job_reports_error_instead_of_rerunning(client, tmp_path):
    """A job left at 'processing' (e.g. after an app restart) must fail cleanly,
    not silently reprocess every file."""
    job_id = _make_job(client, tmp_path, file_count=2)

    # Simulate a job that was mid-flight when the process died.
    jobs_db.update_job_status(job_id, JobStatus.PROCESSING)

    events = _read_stream(client, job_id)
    assert events[-1]["event"] == "job_error"
    assert "interrupt" in events[-1]["error"].lower()

    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "failed"
    assert len(client.get(f"/api/jobs/{job_id}/files").json()) == 0, "stale job must not reprocess files"


def test_subscribe_emits_heartbeat_while_idle():
    """SSE must emit heartbeats while waiting so proxies/EventSource don't time out."""
    from backend.engine.job_manager import JobManager

    gate = threading.Event()

    class SlowProcessor:
        def run_job_generator(self, job_id):
            yield {"event": "job_started", "job_id": job_id, "total_files": 0}
            gate.wait(timeout=10)
            yield {"event": "job_completed", "job_id": job_id, "total_files": 0}

    manager = JobManager(db=None, processor_factory=SlowProcessor)
    manager.ensure_started("job-x")
    threading.Timer(0.6, gate.set).start()

    events = list(manager.subscribe("job-x", heartbeat_interval=0.15))

    kinds = [e["event"] for e in events]
    assert kinds.count("heartbeat") >= 2, f"expected heartbeats while idle, got {kinds}"
    assert kinds[-1] == "job_completed"
