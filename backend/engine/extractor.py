from pathlib import Path
import fitz
import docx
import openpyxl

def extract_pdf_text_layer(file_path: Path) -> str:
    """Fast pass: read the embedded PDF text layer (no OCR).

    Returns "" when the PDF is image-only or cannot be read; the caller then
    queues it for the background OCR layer.
    """
    file_path = Path(file_path)
    try:
        with fitz.open(str(file_path)) as doc:
            parts = [page.get_text() for page in doc]
        return "\n".join(t for t in parts if t).strip()
    except Exception:
        return ""

def extract_direct_text(file_path: Path) -> str:
    """
    Directly extracts text from Word (.docx) or Excel (.xlsx) files.

    PDFs are intentionally NOT handled here: every PDF goes through the
    RapidOCR pipeline (see backend.engine.ocr.extract_pdf_ocr_text),
    regardless of whether it has an embedded text layer.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in (".docx", ".doc"):
        try:
            doc = docx.Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text.strip())
            return "\n".join(paragraphs).strip()
        except Exception:
            return ""

    elif suffix in (".xlsx", ".xls"):
        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            lines = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(val).strip() for val in row if val is not None and str(val).strip()]
                    if row_vals:
                        lines.append(" | ".join(row_vals))
            return "\n".join(lines).strip()
        except Exception:
            return ""

    return ""
