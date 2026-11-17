import json
import shutil
import tempfile
import threading
import time
from pathlib import Path
import queue
import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont
import fitz

from backend.engine.ocr import extract_ocr_text, extract_pdf_ocr_text

def test_extract_ocr_image():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = Path(f.name)
    try:
        # Create a synthetic white image with high contrast black text
        img = Image.new("RGB", (600, 200), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 40), "REPUBLIKA NG PILIPINAS", fill="black")
        draw.text((20, 80), "DRIVER LICENSE REST 1 2", fill="black")
        draw.text((20, 120), "LIC NO: N01-20-123456", fill="black")
        img.save(str(path))

        text = extract_ocr_text(path)
        assert len(text) > 0
        assert "PILIPINAS" in text or "DRIVER" in text or "LICENSE" in text
    finally:
        if path.exists():
            path.unlink()

def test_extract_pdf_ocr():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_f:
        img_path = Path(img_f.name)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_f:
        pdf_path = Path(pdf_f.name)
    try:
        # Create an image, insert into a PDF with no digital text
        img = Image.new("RGB", (500, 200), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 50), "PHILIPPINE PASSPORT DFA", fill="black")
        img.save(str(img_path))

        doc = fitz.open()
        page = doc.new_page(width=500, height=200)
        page.insert_image(page.rect, filename=str(img_path))
        doc.save(str(pdf_path))
        doc.close()

        text = extract_pdf_ocr_text(pdf_path)
        assert len(text) > 0
        assert "PASSPORT" in text or "PHILIPPINE" in text or "DFA" in text
    finally:
        if img_path.exists():
            img_path.unlink()
        if pdf_path.exists():
            pdf_path.unlink()


class _FakeStdin:
    def __init__(self, worker, delay):
        self._worker = worker
        self._delay = delay

    def write(self, payload):
        req = json.loads(payload)
        threading.Timer(
            self._delay,
            lambda: self._worker.out_queue.put(json.dumps({"text": f"text-for-{Path(req['path']).name}"})),
        ).start()

    def flush(self):
        pass


class _FakeStdout:
    def __init__(self, worker):
        self._worker = worker

    def readline(self):
        return self._worker.out_queue.get(timeout=5)


class _FakeWorker:
    """Stands in for the OCR subprocess: responds after a fixed delay."""

    def __init__(self, delay=0.3):
        self.out_queue = queue.Queue()
        self.stdin = _FakeStdin(self, delay)
        self.stdout = _FakeStdout(self)
        self.killed = False

    def poll(self):
        return 0 if self.killed else None

    def kill(self):
        self.killed = True


def test_concurrent_ocr_requests_use_separate_workers(monkeypatch):
    """Two OCR requests in flight at the same time must not serialize on one
    worker process — each gets its own worker from the pool."""
    from backend.engine import ocr

    spawned = []

    def fake_spawn():
        worker = _FakeWorker(delay=0.3)
        spawned.append(worker)
        return worker

    monkeypatch.setattr(ocr, "_spawn_worker", fake_spawn)
    monkeypatch.setattr(ocr, "_ocr_pool", None)  # force a fresh pool

    results = {}
    errors = []

    def run(name, path):
        try:
            results[name] = ocr._ocr_via_worker("img", Path(path))
        except Exception as exc:  # pragma: no cover - surfaced via assertion below
            errors.append(exc)

    t1 = threading.Thread(target=run, args=("a", "page_a.png"))
    t2 = threading.Thread(target=run, args=("b", "page_b.png"))
    started = time.time()
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    elapsed = time.time() - started

    assert not errors, errors
    assert len(results) == 2, "both OCR requests should complete"
    assert len(spawned) >= 2, (
        "concurrent OCR requests were serialized onto a single worker "
        f"(workers spawned={len(spawned)})"
    )
    assert elapsed < 0.9, f"requests ran serially (elapsed={elapsed:.2f}s)"


def test_preprocess_caps_image_for_fast_ocr():
    """OCR input must stay at the optimized 1024px profile.

    An uncommitted change raised the cap to 3600px, sending ~12x more pixels
    through detection/recognition and making pages take tens of seconds.
    """
    from backend.engine.ocr import preprocess_image

    page = np.full((3508, 2480, 3), 245, dtype=np.uint8)  # A4 @ 300 DPI
    out = preprocess_image(page)
    assert max(out.shape[:2]) <= 1024, (
        f"OCR input not downscaled to the optimized profile: {out.shape[:2]}"
    )


def test_pdf_pages_rendered_at_optimized_resolution(tmp_path):
    """PDF pages are rasterized at the fast 150-DPI profile (A4 long edge
    ~1754px); the regression rendered at 300 DPI (~3509px)."""
    from backend.engine.ocr import _render_pdf_pages

    pdf_path = tmp_path / "page.pdf"
    doc = fitz.open()
    doc.new_page()  # A4: 595x842 pt
    doc.save(str(pdf_path))
    doc.close()

    page_paths, tmp_dir = _render_pdf_pages(pdf_path, max_pages=1)
    try:
        assert len(page_paths) == 1
        img = np.fromfile(str(page_paths[0]), dtype=np.uint8)
        rendered = cv2_imdecode(img)
        assert max(rendered.shape[:2]) <= 1800, (
            f"page rasterized too large for the optimized profile: {rendered.shape[:2]}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def cv2_imdecode(buf):
    import cv2
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    assert img is not None
    return img
