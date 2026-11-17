import os
import tempfile
import pytest
from pathlib import Path
from backend.models import JobCreate, JobStatus, FileClassification
from backend.database import DatabaseManager

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        try:
            os.remove(db_path)
        except Exception:
            pass

def test_database_init_and_job_lifecycle(temp_db):
    db = DatabaseManager(temp_db)
    db.init_db()

    # 1. Create a job
    job = db.create_job(
        source_path="C:/test/source",
        output_path="C:/test/output",
        mode="copy",
        threshold=0.70,
        template="{owner}/{doc_type}/"
    )
    assert job.id is not None
    assert job.status == JobStatus.PENDING
    assert job.total_files == 0

    # 2. Update job status and file count
    db.update_job_status(job.id, status=JobStatus.PROCESSING, total_files=5)
    updated = db.get_job(job.id)
    assert updated.status == JobStatus.PROCESSING
    assert updated.total_files == 5

    # 3. Add classified files
    fc1 = FileClassification(
        original_path="C:/test/source/Juan/dl.jpg",
        file_name="dl.jpg",
        doc_type="Driver's License",
        owner="Juan Dela Cruz",
        confidence=95.0,
        destination_path="C:/test/output/Juan Dela Cruz/Driver's License/dl.jpg",
        status="sorted",
        is_unsorted=False
    )
    fc2 = FileClassification(
        original_path="C:/test/source/Juan/random.png",
        file_name="random.png",
        doc_type="Unsorted",
        owner="Juan Dela Cruz",
        confidence=20.0,
        destination_path="C:/test/output/Unsorted/Juan Dela Cruz/random.png",
        status="unsorted",
        is_unsorted=True
    )
    db.add_job_file(job.id, fc1)
    db.add_job_file(job.id, fc2)

    files = db.get_job_files(job.id)
    assert len(files) == 2
    assert files[0].doc_type == "Driver's License"
    assert files[1].is_unsorted is True

    # 4. Complete job
    db.complete_job(job.id, sorted_count=1, unsorted_count=1, duration_seconds=2.5)
    completed = db.get_job(job.id)
    assert completed.status == JobStatus.COMPLETED
    assert completed.sorted_files == 1
    assert completed.unsorted_files == 1
    assert completed.duration_seconds == 2.5
