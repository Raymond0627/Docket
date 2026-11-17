import pytest
from backend.config import load_rules
from backend.engine.classifier import classify_document

@pytest.fixture
def rules():
    return load_rules()

def test_classify_driver_license(rules):
    text = """
    REPUBLIKA NG PILIPINAS
    DEPARTMENT OF TRANSPORTATION
    LAND TRANSPORTATION OFFICE
    DRIVER'S LICENSE
    Lic. No.: D02-18-004521
    Expiration: 2028-10-14
    REST: 1, 2
    """
    result = classify_document(text, rules, threshold=70.0)
    assert result.is_unsorted is False
    assert result.doc_type == "Driver's License"
    assert result.confidence >= 75.0
    assert len(result.matched_keywords) > 0

def test_classify_philsys_national_id(rules):
    text = """
    REPUBLIKA NG PILIPINAS
    Philippine Identification Card
    PhilSys Card Number: 1234-5678-9012-3456
    """
    result = classify_document(text, rules, threshold=70.0)
    assert result.is_unsorted is False
    assert result.doc_type == "PhilSys / National ID"
    assert result.confidence >= 75.0

def test_classify_payslip(rules):
    text = """
    ACME CORPORATION - PAY SLIP
    Period: Oct 1 - Oct 15, 2026
    Basic Salary: P 45,000.00
    Earnings: P 48,000.00
    Deductions: P 5,200.00
    SSS Contribution: P 1,125.00
    PhilHealth Contribution: P 900.00
    Net Pay: P 42,800.00
    """
    result = classify_document(text, rules, threshold=70.0)
    assert result.is_unsorted is False
    assert result.doc_type == "Payslip"
    assert result.confidence >= 75.0

def test_classify_fuzzy_ocr_typos(rules):
    # OCR noise: slight typos in keywords
    text = """
    REPUBLIKA NG PILIPINAS
    LND TRNSPORTATION OFFCE
    DRIVERS LCENSE
    REST 1 2
    """
    result = classify_document(text, rules, threshold=65.0)
    assert result.is_unsorted is False
    assert result.doc_type == "Driver's License"

def test_classify_ambiguous_goes_to_unsorted(rules):
    text = "Just a grocery grocery receipt with no government ID or formal keywords"
    result = classify_document(text, rules, threshold=70.0)
    assert result.is_unsorted is True
    assert result.doc_type == "Unsorted"
    assert result.confidence < 70.0
