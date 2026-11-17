from pathlib import Path

import fitz
from PIL import Image, ImageDraw

from backend.config import load_rules
from backend.database import DatabaseManager
from backend.engine.processor import JobProcessor
from backend.models import AppSettings, JobStatus


def _make_env(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()
    db = DatabaseManager(tmp_path / "test.db")
    db.init_db()
    job = db.create_job(
        source_path=str(src), output_path=str(out),
        mode="copy", threshold=70.0,
    )
    return src, out, db, job


def _digital_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Land Transportation Office\nDriver's License\nLic. No.: D02-18-004521")
    doc.save(str(path))
    doc.close()


def _scan_image(path: Path):
    img = Image.new("RGB", (500, 200), "white")
    ImageDraw.Draw(img).text((20, 60), "PHILIPPINE PASSPORT DFA", fill="black")
    img.save(str(path))


def test_fast_pass_queues_scan_then_background_ocr(tmp_path, monkeypatch):
    src, out, db, job = _make_env(tmp_path)
    _digital_pdf(src / "license.pdf")
    _scan_image(src / "passport.png")
    monkeypatch.setattr(
        "backend.engine.processor.extract_ocr_text",
        lambda *a, **k: "PASSPORT Department of Foreign Affairs Surname Passport No P1234567A",
    )

    events = []
    at_fast = None
    for event in JobProcessor(db=db, rules=load_rules()).run_job_generator(job.id):
        events.append(event)
        if event["event"] == "fast_pass_completed":
            at_fast = {f.file_name: f for f in db.get_job_files(job.id)}

    assert at_fast is not None
    assert at_fast["license.pdf"].status == "sorted"
    assert at_fast["passport.png"].status == "queued"
    assert "Unsorted" in at_fast["passport.png"].destination_path

    kinds = [e["event"] for e in events]
    assert "fast_pass_completed" in kinds
    assert "file_updated" in kinds
    assert kinds.index("fast_pass_completed") < kinds.index("file_updated")

    final = {f.file_name: f for f in db.get_job_files(job.id)}
    assert final["passport.png"].doc_type == "Philippine Passport"
    assert final["passport.png"].stage == "ocr"
    assert final["passport.png"].status == "sorted"
    assert "Unsorted" not in final["passport.png"].destination_path
    assert Path(final["passport.png"].destination_path).exists()
    assert not list((out / "Unsorted").rglob("passport.png"))
    assert db.get_job(job.id).status == JobStatus.COMPLETED


def test_ai_fallback_sorts_ocr_unsorted_file(tmp_path, monkeypatch):
    src, _, db, job = _make_env(tmp_path)
    _scan_image(src / "mystery.png")
    monkeypatch.setattr(
        "backend.engine.processor.extract_ocr_text",
        lambda *a, **k: "totally unknown content",
    )
    monkeypatch.setattr(
        "backend.engine.processor.classify_document_with_gemini",
        lambda **kw: {"doc_type": "Invoice", "owner": "Test Owner", "confidence": 92},
    )
    monkeypatch.setattr(
        "backend.engine.processor.load_settings",
        lambda: AppSettings(ai_fallback_enabled=True, gemini_api_key="dummy"),
    )

    list(JobProcessor(db=db, rules=load_rules()).run_job_generator(job.id))

    final = {f.file_name: f for f in db.get_job_files(job.id)}
    assert final["mystery.png"].doc_type == "Invoice"
    assert final["mystery.png"].stage == "ai"
    assert final["mystery.png"].status == "sorted"
    assert final["mystery.png"].destination_path
    assert db.get_job(job.id).sorted_files == 1
