import tempfile
from pathlib import Path
import docx
import openpyxl

from backend.engine.extractor import extract_direct_text

def test_extract_docx():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = Path(f.name)
    try:
        doc = docx.Document()
        doc.add_heading("Certificate of Employment", level=1)
        doc.add_paragraph("This is to certify that Juan Dela Cruz was employed from 2020 to 2025.")
        doc.save(str(path))

        text = extract_direct_text(path)
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

        text = extract_direct_text(path)
        assert "Employee Name" in text
        assert "Maria Santos" in text
        assert "Basic Salary" in text
    finally:
        if path.exists():
            path.unlink()

def test_pdf_is_not_handled_by_direct_extractor():
    """PDFs must always go through RapidOCR, never the text-layer path."""
    import fitz

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        path = Path(f.name)
    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Republic of the Philippines\nLand Transportation Office")
        doc.save(str(path))
        doc.close()

        assert extract_direct_text(path) == ""
    finally:
        if path.exists():
            path.unlink()
