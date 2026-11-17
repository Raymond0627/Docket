import re
from pathlib import Path
from rapidfuzz import fuzz

from backend.engine.default_roster import DEFAULT_VALIDATED_CUSTOMERS
from backend.models import ValidatedCustomer

GENERIC_FOLDERS = {
    "customers", "clients", "scans", "scanned documents", "scanned docs",
    "batch", "batch 1", "batch 2", "batch-1", "batch-2", "uploads",
    "input", "documents", "files", "valid id", "valid ids", "ids", "id",
    "docket", "temp", "tmp", "new folder", "archive", "test docs", "loose applications batch",
    "sample", "samples", "sample docs", "sample documents", "sample files",
    "test documents", "test files", "batch files"
}

NAME_FILE_NOISE = {
    "scan", "scanned", "pdf", "doc", "document", "bank", "statement",
    "contract", "invoice", "passport", "drivers", "driver", "license",
    "national", "id", "utility", "bill", "tax", "form", "receipt",
    "medical", "resume", "cv", "copy", "final", "signed", "flyer",
    "note", "recipe", "blank", "coffee", "img", "image",
}

NAME_REGEXES = [
    re.compile(r"\b(?:Customer\s*Name|Employee(?:'s)?\s*Name|Member\s*Name|Cardholder\s*Name|Taxpayer\s*Name)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\b(?:Full\s*Name|Pangalan)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\bName\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\b(?:certify\s+that|certifies\s+that)\s+(?:MR\.|MS\.|MRS\.)?\s*([A-Za-z\s\.]+?)(?:,\s*of|\s+is|\s+was)", re.IGNORECASE),
    re.compile(r"\b(?:issued\s+to|granted\s+to)\s+(?:MR\.|MS\.|MRS\.)?\s*([A-Za-z\s\.]+?)(?:,\s*of|\s+for|\s+this)", re.IGNORECASE),
    re.compile(r"\band\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*\(\s*[\"']?Client", re.IGNORECASE),
    re.compile(r"\bBill\s*To\s*[:=]?\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\bAccount\s*(?:Name|Holder)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\bName\s*of\s*(?:Customer|Account\s*Holder|Insured)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
]


def clean_owner_name(name: str) -> str:
    # First line only
    first_line = name.split('\n')[0]
    # Strip any trailing labels
    cleaned = re.split(r"(?:Date|DOB|Address|Sex|Birth|Account|Period|Service|Expiration|REST|Conditions|Tirahan|Kasarian|Kapanganakan)", first_line, flags=re.IGNORECASE)[0].strip()
    cleaned = re.sub(r"[^\w\s,\.\-]", "", cleaned).strip()
    cleaned = " ".join(cleaned.split())
    return cleaned


def normalize_owner_name(name: str) -> str:
    """Canonical display form: "BILL GAYTES" / "bill gAYtes" -> "Bill Gaytes"."""
    cleaned = clean_owner_name(name)
    if not cleaned:
        return cleaned
    words = []
    for word in cleaned.split():
        chunks = []
        for chunk in word.split("-"):
            parts = chunk.split("'")
            chunks.append("'".join(
                p[:1].upper() + p[1:].lower() if p else p for p in parts
            ))
        words.append("-".join(chunks))
    return " ".join(words)


def find_validated_customer(name: str, validated_customers: list) -> str | None:
    """Check if a detected name matches a validated customer or its aliases.
    
    Returns the canonical customer name if found, None otherwise.
    """
    if not name or not validated_customers:
        return None
    
    name_lower = name.strip().lower()
    
    for vc in validated_customers:
        # Check canonical name
        cname = vc.get("name") if isinstance(vc, dict) else getattr(vc, "name", None)
        if cname and name_lower == str(cname).strip().lower():
            return str(cname).strip()
        # Check aliases
        aliases = (vc.get("aliases") if isinstance(vc, dict) else getattr(vc, "aliases", None)) or []
        for alias in aliases:
            if name_lower == str(alias).strip().lower():
                return str(cname).strip() if cname else None
    # Fuzzy fallback for OCR typos.
    best = None
    best_score = 0
    for vc in validated_customers:
        cname = getattr(vc, "name", None) if not isinstance(vc, dict) else vc.get("name")
        if not cname:
            continue
        cname = str(cname).strip()
        aliases = (getattr(vc, "aliases", None) if not isinstance(vc, dict) else vc.get("aliases")) or []
        for cand in [cname] + [str(a) for a in aliases]:
            s = max(
                fuzz.ratio(name_lower, cand.strip().lower()),
                fuzz.token_set_ratio(name_lower, cand.strip().lower()),
            )
            if s > best_score:
                best_score = s
                best = cname
    if best is not None and best_score >= 80:
        return best
    return None


def detect_owner(relative_path: Path, text: str = "", validated_customers: list | None = None) -> str:
    """
    Detects document owner from the relative folder hierarchy or document text.
    Returns 'General' if no confident owner is found.
    """
    parts = list(Path(relative_path).parts)[:-1]  # Exclude filename
    if validated_customers is None:
        vc = DEFAULT_VALIDATED_CUSTOMERS
    else:
        vc = validated_customers

    # 1. Inspect subfolder names from innermost to outermost
    for part in reversed(parts):
        normalized = part.strip().lower()
        if normalized not in GENERIC_FOLDERS and not re.match(r"^batch[\s\-_]?\d+$", normalized):
            clean_part = clean_owner_name(part)
            if len(clean_part) >= 3:
                detected = normalize_owner_name(clean_part)
                matched = find_validated_customer(detected, vc)
                if matched:
                    return matched
                if not vc:
                    return detected

    # 2. Check for name patterns in document text
    if text:
        m_mrz = re.search(r"P<[A-Z]{3}([A-Z]+)<<([A-Z<]+)", text)
        if m_mrz:
            sur = m_mrz.group(1).replace("<", " ").strip()
            giv = m_mrz.group(2).replace("<", " ").strip()
            detected = normalize_owner_name(f"{giv} {sur}")
            matched = find_validated_customer(detected, vc)
            if matched:
                return matched
            if not vc:
                    return detected

        m_lnfn = re.search(r"\bLN\s*\n+([A-Z\s]+)\n+FN\s*\n+([A-Z\s]+)", text)
        if m_lnfn:
            detected = normalize_owner_name(
                f"{clean_owner_name(m_lnfn.group(2))} {clean_owner_name(m_lnfn.group(1))}"
            )
            matched = find_validated_customer(detected, vc)
            if matched:
                return matched
            if not vc:
                    return detected

        # Check two-line Surname / Given Names (e.g. Passport or PhilSys ID)
        m_paired = re.search(r"(?:Surname|Apelyido)[^\n]*\n+([A-Za-z\s]+)\n+(?:Given\s*Names?|Mga\s*Pangalan)[^\n]*\n+([A-Za-z\s]+)", text, re.I)
        if m_paired:
            sur = clean_owner_name(m_paired.group(1))
            giv = clean_owner_name(m_paired.group(2))
            if len(sur) >= 2 and len(giv) >= 2:
                detected = normalize_owner_name(f"{giv} {sur}")
                matched = find_validated_customer(detected, vc)
                if matched:
                    return matched
                if not vc:
                    return detected

        for pattern in NAME_REGEXES:
            match = pattern.search(text)
            if match:
                extracted = clean_owner_name(match.group(1))
                if len(extracted) >= 4:
                    detected = normalize_owner_name(extracted)
                    matched = find_validated_customer(detected, vc)
                    if matched:
                        return matched
                    if not vc:
                        return detected

    # 3. Standalone person-name line near the top (e.g. "Bill Gaytes").
    if text:
        blocked = (
            "bank", "statement", "invoice", "receipt", "account", "form",
            "clearance", "certificate", "insurance", "company", "office",
            "department", "barangay", "school", "hospital", "clinic",
            "policy", "contract", "agreement", "payslip", "employment",
            "tax", "government", "republic", "license", "passport", "id",
            "billing", "bill to", "report", "summary", "history", "medical",
            "resume", "period", "date", "address", "transfer", "debit",
            "credit", "balance", "testland", "testlander", "tst",
            "sample", "power", "water", "co", "company", "supplies", "specimen",
            "test", "testco", "store", "fake", "food", "monthly",
            "bll", "tec", "bategf", "erth", "type", "code", "last", "se",
            "garage", "sale", "grandmas", "pancakes", "unknown", "utility",
        )
        for line in text.splitlines()[:6]:
            candidate = clean_owner_name(line)
            words = candidate.split()
            if not (2 <= len(words) <= 4):
                continue
            if any(ch.isdigit() for ch in candidate):
                continue
            cand_words = set(candidate.lower().split())
            if any(" " in w and w in candidate.lower() for w in blocked) or (cand_words & set(w for w in blocked if " " not in w)):
                continue
            if all(w[0].isupper() for w in words) and len(candidate) >= 5:
                detected = normalize_owner_name(candidate)
                matched = find_validated_customer(detected, vc)
                if matched:
                    return matched
                if not vc:
                    return detected

    # 4. Last resort: a person name encoded in the filename.
    tokens = re.split(r"[^a-z]+", Path(relative_path).stem.lower())
    while tokens and (not tokens[-1] or tokens[-1] in NAME_FILE_NOISE or tokens[-1].isdigit()):
        tokens.pop()
    leading_noise = NAME_FILE_NOISE - {"bill"}
    while tokens and (not tokens[0] or tokens[0] in leading_noise or tokens[0].isdigit()):
        tokens.pop(0)
    words = [t for t in tokens if t.isalpha() and len(t) >= 2]
    if 2 <= len(words) <= 4 and all(w not in GENERIC_FOLDERS for w in words):
        detected = normalize_owner_name(" ".join(words))
        matched = find_validated_customer(detected, vc)
        if matched:
            return matched
        if not vc:
            return detected

    return "General"