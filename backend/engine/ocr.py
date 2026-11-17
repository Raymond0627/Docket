import cv2
import numpy as np
from pathlib import Path
from typing import Optional
import fitz

def get_ocr_dpi() -> int:
    """Resolve the OCR render DPI from saved settings (falls back to 150)."""
    try:
        from backend.config import load_settings
        dpi = int(load_settings().ocr_dpi)
    except Exception:
        dpi = 150
    return max(50, min(600, dpi))

_ocr_engine = None

def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Preprocess image for better OCR accuracy and speed."""
    h, w = img.shape[:2]
    # Optimized OCR profile: keep images at/below 1024px. Larger inputs make
    # detection/recognition dramatically slower (3600px pages took tens of
    # seconds each) for no accuracy gain on ordinary documents.
    max_dim = 1024
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    # Light denoise keeps low-quality scans readable without blurring text
    gray = cv2.bilateralFilter(gray, 5, 50, 50)
    # Contrast enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced

def extract_ocr_text_from_array(img_array: np.ndarray) -> str:
    """Runs RapidOCR on a numpy image array."""
    engine = get_ocr_engine()
    processed = preprocess_image(img_array)
    results, _ = engine(processed)
    if not results:
        return ""
    lines = [item[1] for item in results if len(item) > 1 and item[1]]
    return "\n".join(lines)

def _extract_ocr_text_local(file_path: Path) -> str:
    """Extracts text from image file using RapidOCR (in-process)."""
    file_path = Path(file_path)
    try:
        # Read with OpenCV handling unicode paths on Windows
        data = np.fromfile(str(file_path), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            return ""
        return extract_ocr_text_from_array(img)
    except Exception:
        return ""

def _extract_pdf_ocr_text_local(file_path: Path, max_pages: int = 5) -> str:
    """Renders PDF pages to images and runs OCR on each page (in-process)."""
    file_path = Path(file_path)
    extracted_lines = []
    try:
        with fitz.open(str(file_path)) as doc:
            for page_idx in range(min(len(doc), max_pages)):
                page = doc[page_idx]
                # Render at the configured OCR DPI (default 150)
                pix = page.get_pixmap(dpi=get_ocr_dpi())
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                text = extract_ocr_text_from_array(img)
                if text:
                    extracted_lines.append(text)
        return "\n".join(extracted_lines)
    except Exception:
        return ""


# --- Watchdog: OCR runs in a worker subprocess because ONNX Runtime can
# --- occasionally deadlock inside session.run(); a stuck C call cannot be
# --- interrupted in-process, so the parent kills and restarts the worker.

import json as _json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

_OCR_TIMEOUT = 480  # seconds per OCR request before the worker is killed


class _OcrSlot:
    """One OCR subprocess; a slot is checked out of the pool per request so
    concurrent OCR work runs in its own process instead of queueing behind a
    single global lock."""

    __slots__ = ("proc",)

    def __init__(self):
        self.proc = None


_ocr_pool: "queue.Queue[_OcrSlot] | None" = None
_ocr_pool_lock = threading.Lock()


def ocr_worker_count() -> int:
    """Number of OCR subprocesses (override: DOCKET_OCR_WORKERS)."""
    env = os.environ.get("DOCKET_OCR_WORKERS")
    if env:
        try:
            return max(1, int(env))
        except ValueError:
            pass
    return max(1, min(4, os.cpu_count() or 1))


def _get_pool() -> "queue.Queue[_OcrSlot]":
    global _ocr_pool
    with _ocr_pool_lock:
        if _ocr_pool is None:
            pool: "queue.Queue[_OcrSlot]" = queue.Queue()
            for _ in range(ocr_worker_count()):
                pool.put(_OcrSlot())
            _ocr_pool = pool
    return _ocr_pool


def _spawn_worker() -> "subprocess.Popen":
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "--ocr-worker"]
    else:
        cmd = [sys.executable, "-m", "backend.engine.ocr_worker"]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        cwd=str(Path(__file__).resolve().parents[2]),
    )


def _ocr_via_worker(op: str, path: Path) -> str:
    pool = _get_pool()
    slot = pool.get()  # blocks only when every worker is busy
    try:
        for attempt in (1, 2):
            if slot.proc is None or slot.proc.poll() is not None:
                slot.proc = _spawn_worker()
            worker = slot.proc
            try:
                worker.stdin.write(_json.dumps({"op": op, "path": str(path)}) + "\n")
                worker.stdin.flush()
                box: dict = {}

                def _read(p=worker, box=box):
                    line = p.stdout.readline()
                    if line:
                        box.update(_json.loads(line))

                t = threading.Thread(target=_read, daemon=True)
                t.start()
                t.join(_OCR_TIMEOUT)
                if t.is_alive():
                    worker.kill()  # ONNX deadlock detected
                    slot.proc = None
                    continue
                return box.get("text", "") or ""
            except Exception:
                try:
                    worker.kill()
                except Exception:
                    pass
                slot.proc = None
                if attempt == 2:
                    return ""
        return ""
    finally:
        pool.put(slot)


def extract_ocr_text(file_path: Path) -> str:
    """Extracts text from image file via the OCR worker (watchdog-guarded)."""
    return _ocr_via_worker("img", Path(file_path))


def _render_pdf_pages(file_path: Path, max_pages: int) -> tuple[list, Path]:
    """Renders PDF pages to temporary PNGs so each page can be OCRed in
    parallel by the worker pool. Returns (page_paths, temp_dir)."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="docket_ocr_"))
    page_paths = []
    with fitz.open(str(file_path)) as doc:
        for page_idx in range(min(len(doc), max_pages)):
            # Render at the configured OCR DPI (default 150)
            pix = doc[page_idx].get_pixmap(dpi=get_ocr_dpi())
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            ok, buf = cv2.imencode(".png", img)
            if not ok:
                continue
            page_path = tmp_dir / f"page_{page_idx:03d}.png"
            buf.tofile(str(page_path))  # tofile handles unicode paths on Windows
            page_paths.append(page_path)
    return page_paths, tmp_dir


def extract_pdf_ocr_text(file_path: Path, max_pages: int = 5) -> str:
    """Extracts text from a scanned PDF: render pages, then OCR them in
    parallel across the worker pool (watchdog-guarded)."""
    try:
        page_paths, tmp_dir = _render_pdf_pages(Path(file_path), max_pages)
    except Exception:
        return ""
    if not page_paths:
        return ""
    try:
        if len(page_paths) == 1:
            texts = [_ocr_via_worker("img", page_paths[0])]
        else:
            with ThreadPoolExecutor(max_workers=len(page_paths)) as pool:
                texts = list(pool.map(lambda p: _ocr_via_worker("img", p), page_paths))
        return "\n".join(t for t in texts if t)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
