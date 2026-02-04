from __future__ import annotations

import random
import re

from groq import Groq

from app.config.settings import settings
from app.models.schemas import ConversationEntry, SessionState

PERSONAS = {
    "young_professional": {
        "name": "Aarav",
        "age": 28,
        "style": "casual, slightly anxious, asks short questions",
        "background": "tech support associate, careful with money",
    },
    "small_business_owner": {
        "name": "Meera",
        "age": 42,
        "style": "polite, practical, a bit busy",
        "background": "runs a small retail store",
    },
    "student": {
        "name": "Rohan",
        "age": 21,
        "style": "informal, confused, uses short sentences",
        "background": "college student",
    },
    "retired": {
        "name": "Kavita",
        "age": 63,
        "style": "formal, cautious, asks for clarification",
        "background": "retired teacher",
    },
}

PHASES = ["trust", "elicit", "extract", "exit"]

CHANNEL_HINTS = ["whatsapp", "sms", "email", "telegram", "call", "phone"]

REQUEST_CUES = [
    "upi",
    "account number",
    "otp",
    "pin",
    "password",
    "link",
    "verify",
]


class Agent:
    def __init__(self) -> None:
        self._client: Groq | None = None
        if settings.groq_api_key:
            self._client = Groq(api_key=settings.groq_api_key)

    def _choose_persona(self, session: SessionState) -> str:
        if session.persona:
            return session.persona
        if session.scam_type == "upi_scam":
            return "young_professional"
        if session.scam_type == "bank_fraud":
            return "retired"
        if session.scam_type == "fake_offer":
            return "student"
        return "small_business_owner"

    def _phase_from_state(self, session: SessionState) -> str:
        if session.total_messages < 4:
            return "trust"
        if session.intelligence.upiIds or session.intelligence.phishingLinks or session.intelligence.phoneNumbers:
            if session.total_messages >= 8:
                return "exit"
            return "extract"
        if session.total_messages < 10:
            return "elicit"
        if session.total_messages < 16:
            return "extract"
        return "exit"

    def _system_prompt(self, persona_key: str, phase: str) -> str:
        persona = PERSONAS[persona_key]
        return (
            "You are roleplaying as a possible victim of a scam attempt. "
            "Never reveal you are an AI or a honeypot. Be human and realistic. "
            "Never provide real sensitive information.\n"
            f"Persona: {persona['name']}, age {persona['age']}, {persona['background']}. "
            f"Style: {persona['style']}.\n"
            f"Phase: {phase}. Build trust, ask questions, and gather details. "
            "Keep replies short and natural. Output only the message text."
        )

    def _update_memory(self, session: SessionState) -> None:
        memory = session.persona_memory or {}
        memory.setdefault("scammer_claims", [])
        memory.setdefault("requested_info", [])
        memory.setdefault("channels", [])

        recent = session.conversation[-10:]
        for entry in recent:
            if entry.sender != "scammer":
                continue
            text = entry.text.lower()
            for cue in REQUEST_CUES:
                if cue in text and cue not in memory["requested_info"]:
                    memory["requested_info"].append(cue)
            for channel in CHANNEL_HINTS:
                if channel in text and channel not in memory["channels"]:
                    memory["channels"].append(channel)
            if "blocked" in text or "suspended" in text or "legal action" in text:
                if text not in memory["scammer_claims"]:
                    memory["scammer_claims"].append(text[:120])

        session.persona_memory = memory

    def _fallback_response(self, phase: str, last_text: str) -> str:
        options = {
            "trust": [
                "Sorry, what exactly is happening?",
                "I am a bit worried. Can you explain?",
                "Why will it be blocked?",
            ],
            "elicit": [
                "Can you send the official message or details?",
                "Which bank is this about?",
                "What do you need from me to check this?",
            ],
            "extract": [
                "Where should I verify? Please send the full steps.",
                "Do you have a number I can call back?",
                "Which UPI ID should I send to?",
            ],
            "exit": [
                "I need to step away. I will get back soon.",
                "My app is not loading. Give me a few minutes.",
                "Let me check with my family and reply.",
            ],
        }
        return random.choice(options.get(phase, options["trust"]))

    def generate_response(self, session: SessionState, latest_message: ConversationEntry) -> str:
        persona_key = self._choose_persona(session)
        self._update_memory(session)
        phase = self._phase_from_state(session)
        session.persona = persona_key
        session.phase = phase

        if not self._client:
            return self._fallback_response(phase, latest_message.text)

        system_prompt = self._system_prompt(persona_key, phase)
        memory = session.persona_memory or {}
        memory_lines = []
        if memory.get("requested_info"):
            memory_lines.append(f"Scammer requested: {', '.join(memory['requested_info'])}.")
        if memory.get("channels"):
            memory_lines.append(f"Preferred channels mentioned: {', '.join(memory['channels'])}.")
        if memory.get("scammer_claims"):
            memory_lines.append("Scammer claims: " + " | ".join(memory["scammer_claims"][:2]) + ".")
        if memory_lines:
            system_prompt = system_prompt + "\nMemory: " + " ".join(memory_lines)
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        for entry in session.conversation[-12:]:
            role = "user" if entry.sender == "scammer" else "assistant"
            messages.append({"role": role, "content": entry.text})
        messages.append({"role": "user", "content": latest_message.text})

        response = self._client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=120,
        )
        content = response.choices[0].message.content.strip()
        return content or self._fallback_response(phase, latest_message.text)


agent = Agent()
