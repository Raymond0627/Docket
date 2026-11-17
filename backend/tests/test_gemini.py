import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_gemini_test_key_missing(client):
    res = client.post("/api/ai/test-key", json={"api_key": ""})
    assert res.status_code == 400
    assert "required" in res.json()["detail"].lower()

def test_gemini_analyze_document_nonexistent(client):
    res = client.post("/api/ai/analyze-document", json={
        "file_path": "C:/non_existent_file_99182.png"
    })
    assert res.status_code == 404

def test_gemini_analyze_document_with_mock(client, tmp_path):
    # Create sample dummy image
    test_img = tmp_path / "license.png"
    test_img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")

    # Mock the gemini_service
    mock_result = {
        "doc_type": "Driver's License",
        "owner": "Raymond Gudito",
        "category": "Identification",
        "reference_number": "N02-19-084215",
        "summary": "Valid Philippine Driver's License issued to Raymond Gudito.",
        "confidence": 98.0
    }

    with patch("backend.api.ai.analyze_document_with_gemini", return_value=mock_result):
        res = client.post("/api/ai/analyze-document", json={
            "file_path": str(test_img),
            "api_key": "dummy_test_key"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["doc_type"] == "Driver's License"
        assert data["owner"] == "Raymond Gudito"
        assert data["reference_number"] == "N02-19-084215"

def test_gemini_chat_with_mock(client, tmp_path):
    test_doc = tmp_path / "payslip.docx"
    test_doc.write_text("Dummy content")

    with patch("backend.api.ai.chat_with_gemini", return_value="The net pay is PHP 42,800.00."):
        res = client.post("/api/ai/chat", json={
            "file_path": str(test_doc),
            "prompt": "What is the net pay?",
            "api_key": "dummy_test_key"
        })
        assert res.status_code == 200
        data = res.json()
        assert "42,800" in data["answer"]
