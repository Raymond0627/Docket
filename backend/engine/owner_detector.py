import re
from pathlib import Path

GENERIC_FOLDERS = {
    "customers", "clients", "scans", "scanned documents", "scanned docs",
    "batch", "batch 1", "batch 2", "batch-1", "batch-2", "uploads",
    "input", "documents", "files", "valid id", "valid ids", "ids", "id",
    "docket", "temp", "tmp", "new folder", "archive", "test docs", "loose applications batch"
}

NAME_REGEXES = [
    re.compile(r"\b(?:Customer\s*Name|Employee(?:'s)?\s*Name|Member\s*Name|Cardholder\s*Name|Taxpayer\s*Name)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\b(?:Full\s*Name|Pangalan)\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\bName\s*[:=]\s*([A-Za-z\s,\.]{4,40})", re.IGNORECASE),
    re.compile(r"\b(?:certify\s+that|certifies\s+that)\s+(?:MR\.|MS\.|MRS\.)?\s*([A-Za-z\s\.]+?)(?:,\s*of|\s+is|\s+was)", re.IGNORECASE),
    re.compile(r"\b(?:issued\s+to|granted\s+to)\s+(?:MR\.|MS\.|MRS\.)?\s*([A-Za-z\s\.]+?)(?:,\s*of|\s+for|\s+this)", re.IGNORECASE)
]

def clean_owner_name(name: str) -> str:
    # First line only
    first_line = name.split('\n')[0]
    # Strip any trailing labels
    cleaned = re.split(r"(?:Date|DOB|Address|Sex|Birth|Account|Period|Service|Expiration|REST|Conditions|Tirahan|Kasarian|Kapanganakan)", first_line, flags=re.IGNORECASE)[0].strip()
    cleaned = re.sub(r"[^\w\s,\.\-]", "", cleaned).strip()
    cleaned = " ".join(cleaned.split())
    return cleaned

def detect_owner(relative_path: Path, text: str = "") -> str:
    """
    Detects document owner from the relative folder hierarchy or document text.
    Returns 'General' if no confident owner is found.
    """
    parts = list(Path(relative_path).parts)[:-1]  # Exclude filename

    # 1. Inspect subfolder names from innermost to outermost
    for part in reversed(parts):
        normalized = part.strip().lower()
        if normalized not in GENERIC_FOLDERS and not re.match(r"^batch[\s\-_]?\d+$", normalized):
            clean_part = clean_owner_name(part)
            if len(clean_part) >= 3:
                return clean_part

    # 2. Check for name patterns in document text
    if text:
        # Check two-line Surname / Given Names (e.g. Passport or PhilSys ID)
        m_paired = re.search(r"(?:Surname|Apelyido)[^\n]*\n+([A-Za-z\s]+)\n+(?:Given\s*Names?|Mga\s*Pangalan)[^\n]*\n+([A-Za-z\s]+)", text, re.I)
        if m_paired:
            sur = clean_owner_name(m_paired.group(1))
            giv = clean_owner_name(m_paired.group(2))
            if len(sur) >= 2 and len(giv) >= 2:
                return f"{giv} {sur}"

        for pattern in NAME_REGEXES:
            match = pattern.search(text)
            if match:
                extracted = clean_owner_name(match.group(1))
                if len(extracted) >= 4:
                    return extracted

    return "General"
