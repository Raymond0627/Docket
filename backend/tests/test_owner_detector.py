from pathlib import Path
import pytest
from backend.engine.owner_detector import detect_owner

def test_detect_owner_from_path():
    # Direct customer subfolder
    p1 = Path("Customers/Juan Dela Cruz/DriverLicense.pdf")
    assert detect_owner(p1, "") == "Juan Dela Cruz"

    # Single level subfolder
    p2 = Path("Raymond Gudito/Valid ID/passport.jpg")
    assert detect_owner(p2, "") == "Raymond Gudito"

def test_detect_owner_skips_generic_folders():
    # Skips "Batch-1", "Scanned Documents", "Uploads"
    p = Path("Scanned Documents/Batch 1/Ana Bautista/payslip.pdf")
    assert detect_owner(p, "") == "Ana Bautista"

def test_detect_owner_from_text_fallback():
    # Path has no specific name (just root or generic)
    p = Path("Scans/document_001.pdf")
    text = "REPUBLIKA NG PILIPINAS\nName: Rodrigo Garcia Mendoza\nDate of Birth: 1985-04-12"
    assert detect_owner(p, text) == "Rodrigo Garcia Mendoza"

def test_detect_owner_default():
    p = Path("scans.pdf")
    text = "Some random text with no name label"
    assert detect_owner(p, text) == "General"
