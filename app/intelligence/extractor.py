from __future__ import annotations

import re

from app.models.schemas import ConversationEntry, ExtractedIntelligence

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
UPI_RE = re.compile(r"[a-z0-9._-]{2,}@[a-z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?\d{1,3})?[\s-]?(\d{10})")
BANK_ACCT_RE = re.compile(r"\b\d{9,18}\b")

SUSPICIOUS_KEYWORDS = [
    "urgent",
    "verify now",
    "account blocked",
    "otp",
    "pin",
    "password",
    "click",
    "suspended",
]


def _uniq(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def extract_intelligence(conversation: list[ConversationEntry]) -> ExtractedIntelligence:
    text = "\n".join(entry.text for entry in conversation if entry.text)

    bank_accounts = BANK_ACCT_RE.findall(text)
    upi_ids = UPI_RE.findall(text)
    phishing_links = URL_RE.findall(text)

    phone_matches = PHONE_RE.findall(text)
    phone_numbers = [match[-10:] for match in phone_matches]

    suspicious = [kw for kw in SUSPICIOUS_KEYWORDS if kw in text.lower()]

    return ExtractedIntelligence(
        bankAccounts=_uniq(bank_accounts),
        upiIds=_uniq(upi_ids),
        phishingLinks=_uniq(phishing_links),
        phoneNumbers=_uniq(phone_numbers),
        suspiciousKeywords=_uniq(suspicious),
    )