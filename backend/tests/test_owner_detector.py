from pathlib import Path
import pytest
from backend.engine.owner_detector import detect_owner

def test_detect_owner_from_path():
    # Direct customer subfolder
    p1 = Path("Customers/Juan Dela Cruz/DriverLicense.pdf")
    assert detect_owner(p1, "", validated_customers=[]) == "Juan Dela Cruz"

    # Single level subfolder
    p2 = Path("Raymond Gudito/Valid ID/passport.jpg")
    assert detect_owner(p2, "") == "Raymond Gudito"

def test_detect_owner_skips_generic_folders():
    # Skips "Batch-1", "Scanned Documents", "Uploads"
    p = Path("Scanned Documents/Batch 1/Ana Bautista/payslip.pdf")
    assert detect_owner(p, "", validated_customers=[]) == "Ana Bautista"

def test_detect_owner_from_text_fallback():
    # Path has no specific name (just root or generic)
    p = Path("Scans/document_001.pdf")
    text = "REPUBLIKA NG PILIPINAS\nName: Rodrigo Garcia Mendoza\nDate of Birth: 1985-04-12"
    assert detect_owner(p, text, validated_customers=[]) == "Rodrigo Garcia Mendoza"

def test_detect_owner_default():
    p = Path("scans.pdf")
    text = "Some random text with no name label"
    assert detect_owner(p, text) == "General"

def test_owner_name_casing_is_canonical():
    from pathlib import Path as P
    assert detect_owner(P("Sample Docs/license.pdf"), "LN\nGAYTES\nFN\nBILL") == "Bill Gaytes"
    assert detect_owner(P("Scans/x.pdf"), "Bill Gaytes\nAccount: 123") == "Bill Gaytes"

def test_owner_from_filename_when_scan_is_blank():
    p = Path("Sample Docs/bill_gaytes_bank_statement_scan.pdf")
    assert detect_owner(p, "") == "Bill Gaytes"

def test_owner_from_passport_mrz():
    p = Path("Scans/passport_scan.pdf")
    assert detect_owner(p, "P<TSTDORSEYY<<JACK<<<\nTST56360111<TST<<") == "Jack Dorseyy"
