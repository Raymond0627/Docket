"""OCR worker subprocess.

Reads one JSON request per line from stdin: {"op": "pdf"|"img", "path": "..."}
Writes one JSON response per line: {"text": "..."}.

Exists because ONNX Runtime can occasionally deadlock inside session.run();
the parent process enforces a timeout and restarts us if that happens.
"""
import json
import os
import sys
from pathlib import Path


def onnx_thread_budget(worker_count: int, cpu_count: int = None) -> int:
    """Intra-op threads each OCR worker may use.

    RapidOCR otherwise defaults to one thread per logical core per session;
    several workers doing that at once oversubscribe the CPU (measured ~2x
    slower overall than a single worker), so the budget is split evenly.
    """
    cpus = cpu_count if cpu_count is not None else (os.cpu_count() or 2)
    workers = max(1, worker_count)
    return max(1, cpus // workers)


def apply_onnx_thread_cap(module, threads: int) -> bool:
    """Patch rapidocr's utils module so sessions it builds are limited to
    `threads` intra-op threads.

    rapidocr calls `InferenceSession(model_path, sess_options=...)` from that
    module's globals; wrapping the class here keeps the change inside this
    process instead of forking the library. Explicit thread settings are left
    alone, and any failure degrades to "no cap" rather than blocking OCR.
    """
    try:
        real = getattr(module, "InferenceSession")
        if getattr(real, "_docket_thread_cap", None) == threads:
            return True

        class CappedSession(real):
            def __init__(self, model_path, sess_options=None, providers=None, **kwargs):
                if sess_options is not None and not getattr(sess_options, "intra_op_num_threads", 0):
                    sess_options.intra_op_num_threads = threads
                super().__init__(model_path, sess_options=sess_options, providers=providers, **kwargs)

        CappedSession._docket_thread_cap = threads
        module.InferenceSession = CappedSession
        return True
    except Exception:
        return False


def _install_thread_cap() -> None:
    """Cap ONNX threads for this worker process; never raises."""
    try:
        from backend.engine.ocr import ocr_worker_count
        import rapidocr_onnxruntime.utils as rutils

        budget = onnx_thread_budget(ocr_worker_count(), os.cpu_count() or 2)
        apply_onnx_thread_cap(rutils, budget)
    except Exception:
        pass


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    _install_thread_cap()
    from backend.engine.ocr import _extract_ocr_text_local, _extract_pdf_ocr_text_local

    # Windowed (PyInstaller) children may have no console stdio; use fds 0/1
    in_f, out_f = sys.stdin, sys.stdout
    if in_f is None or not hasattr(in_f, "read"):
        import os
        in_f = os.fdopen(os.dup(0), "r", encoding="utf-8", errors="replace")
    if out_f is None or not hasattr(out_f, "write"):
        import os
        out_f = os.fdopen(os.dup(1), "w", encoding="utf-8")

    for line in in_f:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            path = Path(req["path"])
            if req["op"] == "pdf":
                text = _extract_pdf_ocr_text_local(path)
            else:
                text = _extract_ocr_text_local(path)
            resp = {"text": text}
        except Exception as e:
            resp = {"text": "", "error": str(e)[:200]}
        out_f.write(json.dumps(resp, ensure_ascii=True) + "\n")
        out_f.flush()


if __name__ == "__main__":
    main()
