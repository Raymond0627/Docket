import tempfile
import threading
import time
from pathlib import Path
import pytest
import docx
import fitz

from backend.database import DatabaseManager
from backend.config import load_rules
from backend.engine.processor import JobProcessor
from backend.models import JobStatus

@pytest.fixture
def temp_env():
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out, tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_f:
        db_path = Path(db_f.name)
        db = DatabaseManager(db_path)
        db.init_db()
        yield Path(src), Path(out), db
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

def test_job_processor_run(temp_env):
    src_dir, out_dir, db = temp_env

    # 1. Create subfolder with customer name
    customer_dir = src_dir / "Raymond Gudito"
    customer_dir.mkdir()

    # File 1: Digital PDF (Driver License)
    dl_pdf = customer_dir / "license.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Republic of the Philippines\nLand Transportation Office\nDriver's License\nLic. No.: D02-18-004521")
    doc.save(str(dl_pdf))
    doc.close()

    # File 2: Word Doc (Payslip)
    payslip_docx = customer_dir / "pay.docx"
    doc_w = docx.Document()
    doc_w.add_heading("PAY SLIP", level=1)
    doc_w.add_paragraph("Basic Salary: 50,000\nEarnings: 55,000\nNet Pay: 48,000\nDeductions: 7,000")
    doc_w.save(str(payslip_docx))

    # Create job in DB
    job = db.create_job(
        source_path=str(src_dir),
        output_path=str(out_dir),
        mode="copy",
        threshold=70.0,
        template="{owner}/{doc_type}/"
    )

    rules = load_rules()
    processor = JobProcessor(db=db, rules=rules)

    events = list(processor.run_job_generator(job.id))
    assert len(events) >= 3  # job_started, file_processed * 2, job_completed

    completed_job = db.get_job(job.id)
    assert completed_job.status == JobStatus.COMPLETED
    assert completed_job.total_files == 2
    assert completed_job.sorted_files == 2
    assert completed_job.unsorted_files == 0

    files = db.get_job_files(job.id)
    assert len(files) == 2
    types = {f.doc_type for f in files}
    assert "Driver's License" in types
    assert "Payslip" in types

    # Verify destination files exist on disk
    dest_files = list(out_dir.rglob("*.*"))
    assert len(dest_files) == 2


def test_job_processes_files_concurrently(temp_env, monkeypatch):
    """Files in a batch must be processed in parallel, not strictly one at a time."""
    import os
    if (os.cpu_count() or 1) < 2:
        pytest.skip("needs at least 2 CPU cores to observe concurrency")

    src_dir, out_dir, db = temp_env

    from backend.engine.processor import JobProcessor
    from backend.config import load_rules

    for i in range(6):
        (src_dir / f"note{i}.txt").write_text("rent payment notes", encoding="utf-8")

    job = db.create_job(
        source_path=str(src_dir),
        output_path=str(out_dir),
        mode="copy",
        threshold=70.0,
        template="{owner}/{doc_type}/"
    )

    lock = threading.Lock()
    active = 0
    max_active = 0
    original = JobProcessor.process_file

    def slow_process(self, *args, **kwargs):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.15)
        result = original(self, *args, **kwargs)
        with lock:
            active -= 1
        return result

    monkeypatch.setattr(JobProcessor, "process_file", slow_process)

    processor = JobProcessor(db=db, rules=load_rules())
    events = list(processor.run_job_generator(job.id))

    assert events[-1]["event"] == "job_completed"
    assert max_active >= 2, f"files were processed one at a time (max concurrency={max_active})"
