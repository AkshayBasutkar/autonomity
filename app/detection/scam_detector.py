from __future__ import annotations

import re
from dataclasses import dataclass

from app.detection.llm_classifier import llm_classifier
from app.config.settings import settings


URGENCY_KEYWORDS = [
    "urgent",
    "immediately",
    "today",
    "now",
    "within hours",
    "expire",
    "deadline",
]

THREAT_KEYWORDS = [
    "blocked",
    "suspended",
    "legal action",
    "penalty",
    "account will be",
    "freeze",
]

SENSITIVE_REQUESTS = [
    "otp",
    "pin",
    "password",
    "card details",
    "account number",
    "upi id",
    "verify",
    "kyc",
    "confirm identity",
]

REWARD_KEYWORDS = [
    "prize",
    "refund",
    "cashback",
    "reward",
    "won",
]

SCAM_TYPES = {
    "bank_fraud": ["bank", "account", "blocked", "suspended", "kyc"],
    "upi_scam": ["upi", "vpa", "collect request"],
    "phishing": ["link", "http", "verify", "login"],
    "fake_offer": ["prize", "refund", "cashback", "gift"],
}

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
UPI_RE = re.compile(r"[a-z0-9._-]{2,}@[a-z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(\+?\d{1,3})?[\s-]?(\d{10})")
BANK_ACCT_RE = re.compile(r"\b\d{9,18}\b")


@dataclass
class ScamDetectionResult:
    score: int
    scam_type: str | None
    suspicious_keywords: list[str]
    llm_confidence: int | None = None


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def detect_scam(text: str) -> ScamDetectionResult:
    suspicious = []
    score = 0

    urgency = _keyword_hits(text, URGENCY_KEYWORDS)
    threat = _keyword_hits(text, THREAT_KEYWORDS)
    sensitive = _keyword_hits(text, SENSITIVE_REQUESTS)
    reward = _keyword_hits(text, REWARD_KEYWORDS)

    url_hits = URL_RE.findall(text)
    upi_hits = UPI_RE.findall(text)
    phone_hits = PHONE_RE.findall(text)

    suspicious.extend(urgency + threat + sensitive + reward)
    if url_hits:
        suspicious.append("phishing link")
    if upi_hits:
        suspicious.append("upi id")
    if phone_hits:
        suspicious.append("phone number")

    score += len(urgency) * 10
    score += len(threat) * 15
    score += len(sensitive) * 20
    score += len(reward) * 10
    score += 25 if url_hits else 0
    score += 15 if upi_hits else 0

    scam_type = None
    text_lower = text.lower()
    for key, signals in SCAM_TYPES.items():
        if any(signal in text_lower for signal in signals):
            scam_type = key
            break
    llm_confidence = None
    if llm_classifier.enabled():
        llm_result = llm_classifier.classify(text)
        if llm_result and isinstance(llm_result, dict):
            llm_confidence = int(min(max(llm_result.get("confidence", 0), 0), 100))
            if llm_result.get("scam") is True:
                score += min(settings.llm_weight, llm_confidence)
                if not scam_type and llm_result.get("scam_type") not in (None, "unknown"):
                    scam_type = llm_result.get("scam_type")
            if llm_result.get("signals"):
                suspicious.extend([str(sig) for sig in llm_result.get("signals")])

    return ScamDetectionResult(
        score=min(score, 100),
        scam_type=scam_type,
        suspicious_keywords=list(dict.fromkeys(suspicious)),
        llm_confidence=llm_confidence,
    )
