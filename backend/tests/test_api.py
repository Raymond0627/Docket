import pytest
from fastapi.testclient import TestClient
from backend.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_rules_endpoints(client):
    res = client.get("/api/rules")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    assert any(r["name"] == "Driver's License" for r in data)

def test_api_settings_endpoints(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "output_path" in data
    assert "confidence_threshold" in data

    # Update settings
    update_payload = {
        "output_path": "./Custom_Output",
        "file_mode": "copy",
        "confidence_threshold": 75.0,
        "folder_template": "{owner}/{doc_type}/",
        "auto_open_explorer": False
    }
    put_res = client.put("/api/settings", json=update_payload)
    assert put_res.status_code == 200
    assert put_res.json()["confidence_threshold"] == 75.0

def test_api_system_open_folder(client):
    # Non-existent path returns 404
    res = client.post("/api/system/open-folder", json={"folder_path": "C:/NonExistentPath_Docket_12345"})
    assert res.status_code == 404

    # Current path returns 200
    import os
    res = client.post("/api/system/open-folder", json={"folder_path": os.getcwd()})
    assert res.status_code == 200
    assert res.json()["success"] is True

def test_api_jobs_upload_files(client):
    # Test uploading multiple files with relative paths
    files = [
        ("files", ("license.pdf", b"%PDF-1.4 dummy pdf content", "application/pdf")),
        ("files", ("pay.docx", b"PK dummy docx content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    ]
    data = {
        "relative_paths": ["Raymond Gudito/license.pdf", "Raymond Gudito/pay.docx"]
    }
    res = client.post("/api/jobs/upload", files=files, data=data)
    assert res.status_code == 200
    job = res.json()
    assert "id" in job
    assert job["status"] == "pending"

def test_api_file_preview(client, tmp_path):
    # Create a test file
    test_img = tmp_path / "sample.png"
    test_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")

    # Preview existing file
    res = client.get("/api/files/preview", params={"path": str(test_img)})
    assert res.status_code == 200
    assert "image/png" in res.headers["content-type"]

    # Non-existent file
    res_404 = client.get("/api/files/preview", params={"path": str(tmp_path / "ghost.png")})
    assert res_404.status_code == 404

def test_api_reclassify_file(client, tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()

    # Create an unsorted file directly in src
    test_file = src / "mystery.txt"
    test_file.write_text("Unrecognized content")

    # Start and run job
    create_res = client.post("/api/jobs", json={
        "source_path": str(src),
        "output_path": str(out),
        "file_mode": "copy",
        "confidence_threshold": 80.0,
        "folder_template": "{owner}/{doc_type}/"
    })
    job_id = create_res.json()["id"]

    # Stream to run job
    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
        for _ in stream.iter_lines():
            pass

    # Verify initial file is unsorted
    files_res = client.get(f"/api/jobs/{job_id}/files")
    files = files_res.json()
    assert len(files) == 1
    f = files[0]
    assert f["is_unsorted"] is True

    # Reclassify file
    reclass_res = client.post(f"/api/jobs/{job_id}/reclassify", json={
        "original_path": f["original_path"],
        "new_doc_type": "Driver's License",
        "new_owner": "Raymond Gudito",
        "target_folder": "Driver License"
    })
    assert reclass_res.status_code == 200
    updated_file = reclass_res.json()["file"]
    assert updated_file["doc_type"] == "Driver's License"
    assert updated_file["owner"] == "Raymond Gudito"
    assert updated_file["is_unsorted"] is False

    # Check that file exists at new destination
    import os
    assert os.path.exists(updated_file["destination_path"])

    # Check updated job metrics
    job_res = client.get(f"/api/jobs/{job_id}")
    job = job_res.json()
    assert job["sorted_files"] == 1
    assert job["unsorted_files"] == 0

def test_api_reorganize_output_structure(client, tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()

    # Create PDF (processed through OCR)
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Republic of the Philippines Land Transportation Office Driver's License Lic. No. N01-20-123456\nName: Raymond Gudito")
    doc.save(str(src / "dl.pdf"))
    doc.close()

    # Create and run job with {owner}/{doc_type}/
    create_res = client.post("/api/jobs", json={
        "source_path": str(src),
        "output_path": str(out),
        "folder_template": "{owner}/{doc_type}/"
    })
    job_id = create_res.json()["id"]

    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
        for _ in stream.iter_lines():
            pass

    # Call reorganize endpoint to switch hierarchy to {doc_type}/{owner}/
    reorg_res = client.post(f"/api/jobs/{job_id}/reorganize", json={
        "folder_template": "{doc_type}/{owner}/"
    })
    assert reorg_res.status_code == 200
    assert reorg_res.json()["success"] is True

    # Verify that file on disk is now in {doc_type}/{owner}/
    files_res = client.get(f"/api/jobs/{job_id}/files")
    f = files_res.json()[0]
    import os
    assert os.path.exists(f["destination_path"])
    assert "Driver License" in f["destination_path"] or "Driver's License" in f["destination_path"]
    assert "Raymond Gudito" in f["destination_path"]


def test_api_analyze_file_with_ai(client, tmp_path, monkeypatch):
    from backend.models import AppSettings

    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()
    mystery = src / "mystery.txt"
    mystery.write_text("unknown content", encoding="utf-8")

    job_id = client.post("/api/jobs", json={
        "source_path": str(src), "output_path": str(out),
    }).json()["id"]
    with client.stream("GET", f"/api/jobs/{job_id}/stream") as stream:
        for _ in stream.iter_lines():
            pass

    monkeypatch.setattr(
        "backend.api.jobs.load_settings",
        lambda: AppSettings(gemini_api_key="dummy"),
    )
    monkeypatch.setattr(
        "backend.api.jobs.classify_document_with_gemini",
        lambda **kw: {"doc_type": "Invoice", "owner": "Test Owner", "confidence": 90},
    )

    res = client.post(f"/api/jobs/{job_id}/analyze", json={"original_path": str(mystery)})
    assert res.status_code == 200
    f = res.json()["file"]
    assert f["doc_type"] == "Invoice"
    assert f["status"] == "sorted"
    assert f["stage"] == "ai"
    assert "Test Owner" in f["destination_path"]
