from __future__ import annotations

import json
from typing import Any

from groq import Groq

from app.config.settings import settings


class LLMScamClassifier:
    def __init__(self) -> None:
        self._client: Groq | None = None
        if settings.groq_api_key:
            self._client = Groq(api_key=settings.groq_api_key)

    def enabled(self) -> bool:
        return self._client is not None and settings.llm_detection_enabled

    def classify(self, text: str) -> dict[str, Any] | None:
        if not self._client:
            return None

        system_prompt = (
            "You are a strict scam detection classifier. "
            "Return JSON only with keys: scam (boolean), confidence (0-100), "
            "scam_type (bank_fraud|upi_scam|phishing|fake_offer|impersonation|other|unknown), "
            "signals (array of short strings)."
        )
        user_prompt = f"Classify this message: {text}"

        response = self._client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None


llm_classifier = LLMScamClassifier()