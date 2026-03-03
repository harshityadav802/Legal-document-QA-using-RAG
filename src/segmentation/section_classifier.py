"""Section classifier — assigns semantic labels to legal document sections."""

import re
from typing import Dict, List

# Keyword clusters per section type
_SECTION_KEYWORDS: Dict[str, List[str]] = {
    "DEFINITIONS": [
        "means", "shall mean", "refers to", "is defined as", "definition",
        "interpret", "interpretation",
    ],
    "PARTIES": [
        "party", "parties", "hereinafter", "referred to as", "entered into",
        "between", "by and between",
    ],
    "RECITALS": ["whereas", "recital", "background", "preamble", "witnesseth"],
    "OBLIGATIONS": [
        "shall", "must", "agrees to", "obligat", "undertake", "covenant",
        "will perform",
    ],
    "PAYMENT": [
        "payment", "fee", "fees", "invoice", "compensation", "remuneration",
        "price", "cost", "taxes", "gst",
    ],
    "TERMINATION": [
        "terminat", "expir", "cancel", "end", "cessation", "notice of termination",
    ],
    "CONFIDENTIALITY": [
        "confidential", "non-disclosure", "nda", "proprietary", "secret",
        "disclose", "disclosure",
    ],
    "IP": [
        "intellectual property", "copyright", "patent", "trademark",
        "ownership", "license", "deliverable",
    ],
    "LIABILITY": [
        "liability", "liable", "damages", "indemnif", "consequential",
        "limitation", "cap on",
    ],
    "DISPUTE": [
        "dispute", "arbitration", "mediation", "litigation", "jurisdiction",
        "governing law", "court",
    ],
    "GENERAL": [
        "general", "miscellaneous", "severability", "waiver", "amendment",
        "entire agreement", "counterpart", "force majeure",
    ],
    "SCHEDULE": ["schedule", "exhibit", "annex", "appendix", "attachment"],
    "SIGNATURE": [
        "in witness whereof", "signed", "executed", "authorized",
        "signature", "by:", "name:", "title:",
    ],
}


def classify_section(heading: str, body: str = "") -> str:
    """Classify a legal section by its heading and optional body text.

    Returns a label from _SECTION_KEYWORDS keys, or 'OTHER'.
    """
    combined = (heading + " " + body[:500]).lower()

    scores: Dict[str, int] = {}
    for label, keywords in _SECTION_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in combined:
                score += 1
        if score:
            scores[label] = score

    if not scores:
        return "OTHER"
    return max(scores, key=lambda k: scores[k])


def is_operative_clause(text: str) -> bool:
    """Return True if the text contains operative legal language."""
    operative_patterns = [
        r"\bshall\b",
        r"\bmust\b",
        r"\bagrees\s+to\b",
        r"\bundertakes\s+to\b",
        r"\bhereby\b",
        r"\bcovenants\s+to\b",
    ]
    for pattern in operative_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def extract_cross_references(text: str) -> List[str]:
    """Extract cross-references like 'Section 5.2', 'Article III', etc."""
    patterns = [
        r"[Ss]ection\s+\d+(?:\.\d+)*",
        r"[Aa]rticle\s+[IVXivx]+|\d+",
        r"[Ss]chedule\s+[A-Z\d]+",
        r"[Ee]xhibit\s+[A-Z\d]+",
        r"[Cc]lause\s+\d+(?:\.\d+)*",
    ]
    refs = []
    for pattern in patterns:
        refs.extend(re.findall(pattern, text))
    return list(set(refs))
