"""Background job execution with replayable SSE subscriptions.

Jobs run in a background thread instead of inside the SSE HTTP request, so a
client disconnect (tab switch, reload, closing the app window mid-job) no
longer aborts processing. Events are buffered per job, which lets any number
of subscribers (re)connect and replay the full history.
"""
import logging
import threading
from typing import Callable, Dict, Iterator, List, Optional

from backend.database import DatabaseManager
from backend.models import JobStatus
from backend.engine.control import clear_job_control

logger = logging.getLogger(__name__)

TERMINAL_EVENTS = ("job_completed", "job_error")


class _JobRun:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.events: List[dict] = []
        self.cond = threading.Condition()
        self.finished = False


class JobManager:
    """Starts each job at most once and fans its events out to subscribers."""

    def __init__(self, db: DatabaseManager, processor_factory: Callable[[], object]):
        self.db = db
        self.processor_factory = processor_factory
        self._runs: Dict[str, _JobRun] = {}
        self._lock = threading.Lock()

    def ensure_started(self, job_id: str) -> _JobRun:
        """Return the live run for job_id, starting it if needed (idempotent)."""
        with self._lock:
            run = self._runs.get(job_id)
            if run is not None:
                return run
            run = _JobRun(job_id)
            self._runs[job_id] = run
        thread = threading.Thread(
            target=self._run,
            args=(run,),
            name=f"docket-job-{job_id[:8]}",
            daemon=True,
        )
        thread.start()
        return run

    def is_running(self, job_id: str) -> bool:
        with self._lock:
            run = self._runs.get(job_id)
        return run is not None and not run.finished

    def subscribe(self, job_id: str, heartbeat_interval: float = 15.0) -> Iterator[dict]:
        """Yield the job's events: replayed history first, then live events.

        Emits heartbeats while idle so the connection is not dropped, and
        recovers gracefully when the run is no longer in memory (e.g. the
        application restarted mid-job).
        """
        run = self._runs.get(job_id)
        if run is None:
            recovery = self._recovery_event(job_id)
            if recovery is None:
                run = self.ensure_started(job_id)
            else:
                yield recovery
                return
        yield from self._stream_run(run, heartbeat_interval)

    def _recovery_event(self, job_id: str) -> Optional[dict]:
        """Terminal event for a job with no live run; None means 'start it'."""
        job = self.db.get_job(job_id)
        if job is None:
            return {"event": "job_error", "job_id": job_id, "error": "Job not found"}
        if job.status == JobStatus.PENDING:
            return None
        if job.status == JobStatus.PROCESSING:
            # Leftover from a previous process: safe reprocessing is not
            # possible (files were already routed), so fail it explicitly.
            try:
                self.db.update_job_status(job_id, JobStatus.FAILED)
            except Exception:  # pragma: no cover - best effort
                logger.exception("Could not mark stale job %s as failed", job_id)
            return {
                "event": "job_error",
                "job_id": job_id,
                "error": "Job was interrupted before completion",
            }
        if job.status == JobStatus.COMPLETED:
            return {
                "event": "job_completed",
                "job_id": job_id,
                "total_files": job.total_files,
                "sorted_files": job.sorted_files,
                "unsorted_files": job.unsorted_files,
                "duration_seconds": job.duration_seconds,
            }
        return {"event": "job_error", "job_id": job_id, "error": "Job failed"}

    def _stream_run(self, run: _JobRun, heartbeat_interval: float) -> Iterator[dict]:
        idx = 0
        while True:
            event = None
            with run.cond:
                if idx >= len(run.events) and not run.finished:
                    run.cond.wait(heartbeat_interval)
                if idx < len(run.events):
                    event = run.events[idx]
                    idx += 1
            if event is None:
                with run.cond:
                    drained = run.finished and idx >= len(run.events)
                if drained:
                    return
                yield {"event": "heartbeat", "job_id": run.job_id}
                continue
            yield event
            if event.get("event") in TERMINAL_EVENTS:
                return

    def _run(self, run: _JobRun) -> None:
        job_id = run.job_id
        try:
            processor = self.processor_factory()
            for event in processor.run_job_generator(job_id):
                self._append(run, event)
        except Exception as exc:
            logger.exception("Job %s failed", job_id)
            try:
                self.db.update_job_status(job_id, JobStatus.FAILED)
            except Exception:  # pragma: no cover - best effort
                logger.exception("Could not mark job %s as failed", job_id)
            self._append(run, {"event": "job_error", "job_id": job_id, "error": str(exc)})
        finally:
            clear_job_control(job_id)
            with run.cond:
                run.finished = True
                run.cond.notify_all()

    @staticmethod
    def _append(run: _JobRun, event: dict) -> None:
        with run.cond:
            run.events.append(event)
            run.cond.notify_all()
