import tempfile
from pathlib import Path
import pytest
import docx
import openpyxl
import fitz

from backend.engine.extractor import extract_direct_text

def test_extract_docx():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = Path(f.name)
    try:
        doc = docx.Document()
        doc.add_heading("Certificate of Employment", level=1)
        doc.add_paragraph("This is to certify that Juan Dela Cruz was employed from 2020 to 2025.")
        doc.save(str(path))

        text, is_digital = extract_direct_text(path)
        assert is_digital is True
        assert "Certificate of Employment" in text
        assert "Juan Dela Cruz" in text
    finally:
        if path.exists():
            path.unlink()

def test_extract_xlsx():
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = Path(f.name)
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws["A1"] = "Employee Name"
        ws["B1"] = "Maria Santos"
        ws["A2"] = "Basic Salary"
        ws["B2"] = 50000
        wb.save(str(path))

        text, is_digital = extract_direct_text(path)
        assert is_digital is True
        assert "Employee Name" in text
        assert "Maria Santos" in text
        assert "Basic Salary" in text
    finally:
        if path.exists():
            path.unlink()

def test_extract_digital_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Republic of the Philippines\nLand Transportation Office\nDriver's License")
        doc.save(str(path))
        doc.close()

        text, is_digital = extract_direct_text(path)
        assert is_digital is True
        assert "Land Transportation Office" in text
        assert "Driver's License" in text
    finally:
        if path.exists():
            path.unlink()

def test_extract_empty_or_scanned_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    try:
        # Create a PDF page with no text (representing a scan)
        doc = fitz.open()
        doc.new_page()
        doc.save(str(path))
        doc.close()

        text, is_digital = extract_direct_text(path)
        assert is_digital is False
        assert len(text.strip()) == 0
    finally:
        if path.exists():
            path.unlink()
