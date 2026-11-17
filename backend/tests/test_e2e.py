import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.seed_demo import create_sample_documents

def test_full_end_to_end_pipeline():
    client = TestClient(app)

    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
        src_path = Path(src)
        out_path = Path(out)

        # Seed sample documents
        create_sample_documents(src_path)

        # 1. Start job via REST API
        create_res = client.post("/api/jobs", json={
            "source_path": str(src_path),
            "output_path": str(out_path),
            "file_mode": "copy",
            "confidence_threshold": 70.0,
            "folder_template": "{owner}/{doc_type}/"
        })
        assert create_res.status_code == 200
        job_data = create_res.json()
        job_id = job_data["id"]

        # 2. Consume SSE stream to run the job to completion
        with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
            events = []
            for line in stream.iter_lines():
                if line.startswith("data: "):
                    events.append(line[6:])
        assert len(events) >= 7

        # 3. Check job final state
        job_res = client.get(f"/api/jobs/{job_id}")
        assert job_res.status_code == 200
        completed = job_res.json()
        assert completed["status"] == "completed"
        assert completed["total_files"] == 6
        assert completed["sorted_files"] == 5
        assert completed["unsorted_files"] == 1

        # 4. Check classified files
        files_res = client.get(f"/api/jobs/{job_id}/files")
        assert files_res.status_code == 200
        files = files_res.json()
        assert len(files) == 6

        # Check types
        type_map = {f["file_name"]: f["doc_type"] for f in files}
        assert type_map["driver_license.pdf"] == "Driver's License"
        assert type_map["payslip_oct2026.docx"] == "Payslip"
        assert type_map["coe_employment.docx"] == "Certificate of Employment (COE)"
        assert type_map["meralco_bill.pdf"] == "Billing Statement / Utility Bill"
        assert type_map["passport_scan.png"] == "Philippine Passport"
        assert type_map["random_notes.docx"] == "Unsorted"

        # 5. Check directory tree
        tree_res = client.get(f"/api/jobs/{job_id}/tree")
        assert tree_res.status_code == 200
        tree = tree_res.json()
        assert tree["type"] == "directory"
        child_names = {c["name"] for c in tree["children"]}
        assert "Raymond Gudito" in child_names
        assert "Maria Santos" in child_names
        assert "Pedro Penduko" in child_names
        assert "Unsorted" in child_names

        # 6. Check CSV report download
        csv_res = client.get(f"/api/jobs/{job_id}/csv")
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "Driver's License" in csv_res.text
        assert "Raymond Gudito" in csv_res.text
        assert "Unsorted" in csv_res.text
