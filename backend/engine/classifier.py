import re
from typing import List, Tuple
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from backend.models import RuleDefinition

class ClassificationResult(BaseModel):
    doc_type: str
    target_folder: str
    confidence: float
    matched_keywords: List[str] = Field(default_factory=list)
    is_unsorted: bool = False

def score_rule(text: str, rule: RuleDefinition) -> Tuple[float, List[str]]:
    """
    Computes a match confidence score (0-100) and list of matched keywords/patterns for a rule.
    """
    if not text or not text.strip():
        return 0.0, []

    matched = []
    text_lower = text.lower()
    regex_matched = False

    # 1. Regex evaluation
    for pattern in rule.regex_patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                regex_matched = True
                matched.append(f"pattern:{pattern}")
                break
        except Exception:
            pass

    # 2. Keyword evaluation
    keyword_matches = 0
    total_keywords = len(rule.keywords) if rule.keywords else 0

    for kw in rule.keywords:
        kw_lower = kw.lower()
        if kw_lower in text_lower:
            keyword_matches += 1
            matched.append(kw)
        else:
            # Fuzzy match for OCR typos. Close matches (>=80) count as a full
            # hit so minor OCR typos do not drag the composite score down.
            score = fuzz.partial_ratio(kw_lower, text_lower)
            if score >= 82:
                keyword_matches += 1.0 if score >= 80 else 0.85
                matched.append(f"{kw} (~{int(score)}%)")

    # 3. Composite score calculation
    if total_keywords > 0:
        kw_ratio = min(1.0, keyword_matches / max(1, min(total_keywords, 4)))
    else:
        kw_ratio = 0.0

    score = 0.0
    if regex_matched and total_keywords > 0:
        score = 40.0 + (kw_ratio * 60.0)
    elif regex_matched:
        score = 85.0
    elif total_keywords > 0:
        score = kw_ratio * 100.0

    return min(100.0, round(score, 1)), matched

def classify_document(
    text: str,
    rules: List[RuleDefinition],
    threshold: float = 70.0
) -> ClassificationResult:
    """
    Classifies extracted text against document rules.
    If no rule meets the confidence threshold, routes to Unsorted.
    """
    best_rule = None
    best_score = 0.0
    best_matched = []

    for rule in rules:
        if not rule.enabled:
            continue
        score, matched = score_rule(text, rule)
        if score > best_score:
            best_score = score
            best_rule = rule
            best_matched = matched

    effective_threshold = max(threshold, best_rule.min_confidence if best_rule else threshold)

    if best_rule and best_score >= effective_threshold:
        return ClassificationResult(
            doc_type=best_rule.name,
            target_folder=best_rule.target_folder,
            confidence=best_score,
            matched_keywords=best_matched,
            is_unsorted=False
        )
    else:
        return ClassificationResult(
            doc_type="Unsorted",
            target_folder="Unsorted",
            confidence=best_score,
            matched_keywords=best_matched,
            is_unsorted=True
        )
