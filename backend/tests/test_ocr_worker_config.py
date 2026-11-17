"""Tests for ONNX thread budgeting inside the OCR worker subprocess.

Without a cap, every OCR worker creates ONNX sessions with one intra-op thread
per logical core. Running several workers at once then oversubscribes the CPU
(4 workers x 16 threads on 16 cores) and measured *slower* overall than doing
nothing in parallel.
"""
import onnxruntime as ort
import pytest

from backend.engine.ocr_worker import apply_onnx_thread_cap, onnx_thread_budget


def test_thread_budget_divides_cores_across_workers():
    assert onnx_thread_budget(worker_count=4, cpu_count=16) == 4
    assert onnx_thread_budget(worker_count=1, cpu_count=16) == 16
    assert onnx_thread_budget(worker_count=8, cpu_count=4) == 1
    assert onnx_thread_budget(worker_count=3, cpu_count=10) == 3


class _FakeSession:
    """Stands in for onnxruntime.InferenceSession (no model loading)."""

    def __init__(self, model_path, sess_options=None, providers=None, **kwargs):
        self.model_path = model_path
        self.sess_options = sess_options


class _FakeRapidOcrUtils:
    InferenceSession = _FakeSession


def test_thread_cap_applies_to_sessions_with_default_options():
    mod = _FakeRapidOcrUtils()
    assert apply_onnx_thread_cap(mod, threads=4) is True

    opts = ort.SessionOptions()  # intra_op_num_threads defaults to 0 (= auto)
    assert opts.intra_op_num_threads == 0

    session = mod.InferenceSession("model.onnx", sess_options=opts, providers=["CPUExecutionProvider"])
    assert session.sess_options.intra_op_num_threads == 4


def test_thread_cap_leaves_explicit_thread_setting_untouched():
    mod = _FakeRapidOcrUtils()
    apply_onnx_thread_cap(mod, threads=4)

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2

    session = mod.InferenceSession("model.onnx", sess_options=opts, providers=[])
    assert session.sess_options.intra_op_num_threads == 2


def test_thread_cap_is_idempotent():
    mod = _FakeRapidOcrUtils()
    first = mod.InferenceSession
    apply_onnx_thread_cap(mod, threads=4)
    second = mod.InferenceSession
    assert second is not first  # wrapped

    # applying again with the same budget must not stack wrappers
    apply_onnx_thread_cap(mod, threads=4)
    assert mod.InferenceSession is second
