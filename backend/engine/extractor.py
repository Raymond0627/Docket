from pathlib import Path
from typing import Tuple
import fitz
import docx
import openpyxl

def extract_direct_text(file_path: Path) -> Tuple[str, bool]:
    """
    Directly extracts text from digital PDF, Word (.docx), or Excel (.xlsx).
    Returns (extracted_text, is_digital).
    If a PDF has less than 20 characters of extractable text, is_digital is False
    signaling it needs OCR.
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        text_parts = []
        try:
            with fitz.open(str(file_path)) as doc:
                for page in doc:
                    t = page.get_text()
                    if t:
                        text_parts.append(t)
            full_text = "\n".join(text_parts).strip()
            # If less than 20 chars, it's likely scanned or image-only
            if len(full_text) >= 20:
                return full_text, True
            return full_text, False
        except Exception:
            return "", False

    elif suffix in (".docx", ".doc"):
        try:
            doc = docx.Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text.strip())
            full_text = "\n".join(paragraphs).strip()
            return full_text, True
        except Exception:
            return "", False

    elif suffix in (".xlsx", ".xls"):
        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            lines = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    row_vals = [str(val).strip() for val in row if val is not None and str(val).strip()]
                    if row_vals:
                        lines.append(" | ".join(row_vals))
            full_text = "\n".join(lines).strip()
            return full_text, True
        except Exception:
            return "", False

    return "", False
