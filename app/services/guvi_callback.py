from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config.settings import settings
from app.models.schemas import ExtractedIntelligence, SessionState


async def send_final_result(session: SessionState) -> bool:
    intelligence = session.intelligence
    payload: dict[str, Any] = {
        "sessionId": session.session_id,
        "sessionld": session.session_id,
        "scamDetected": session.scam_detected,
        "totalMessagesExchanged": session.total_messages,
        "extractedIntelligence": intelligence.model_dump(),
        "agentNotes": session.agent_notes,
    }

    backoff = 1.0
    for _ in range(3):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(settings.guvi_callback_url, json=payload)
                if response.status_code < 400:
                    return True
        except httpx.HTTPError:
            pass
        await asyncio.sleep(backoff)
        backoff *= 2
    return False