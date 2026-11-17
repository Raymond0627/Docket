"""Per-file cancellation for the layered processing pipeline.

The fast pass identifies files that need background OCR/AI. While that work
runs, the user may manually classify a file from the Results screen. Cancelling
uses a per-file threading.Event so:

- queued files are skipped before their OCR starts,
- an OCR request that is already in flight kills its worker process and is
  discarded (see backend.engine.ocr),
- the routing step re-checks under a job lock so a manual override can never
  race with background routing.
"""
import threading
from typing import Dict, Optional


class JobControl:
    def __init__(self, job_id: str):
        self.job_id = job_id
        # Serializes "check cancelled + route file" against manual overrides.
        self.lock = threading.RLock()
        self._events: Dict[str, threading.Event] = {}

    def event_for(self, original_path) -> threading.Event:
        key = str(original_path)
        with self.lock:
            event = self._events.get(key)
            if event is None:
                event = threading.Event()
                self._events[key] = event
            return event

    def cancel(self, original_path) -> None:
        self.event_for(original_path).set()

    def is_cancelled(self, original_path) -> bool:
        return self.event_for(original_path).is_set()


_registry: Dict[str, JobControl] = {}
_registry_lock = threading.Lock()


def get_job_control(job_id: str) -> JobControl:
    with _registry_lock:
        control = _registry.get(job_id)
        if control is None:
            control = JobControl(job_id)
            _registry[job_id] = control
        return control


def peek_job_control(job_id: str) -> Optional[JobControl]:
    with _registry_lock:
        return _registry.get(job_id)


def clear_job_control(job_id: str) -> None:
    with _registry_lock:
        _registry.pop(job_id, None)
