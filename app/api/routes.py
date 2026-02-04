from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config.settings import settings
from app.core.manager import handle_message
from app.models.schemas import MessageRequest, MessageResponse
from app.services.session_store import session_store

router = APIRouter()


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@router.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/message", response_model=MessageResponse)
async def message_endpoint(
    payload: MessageRequest,
    _: None = Depends(verify_api_key),
) -> MessageResponse:
    return await handle_message(payload)


@router.get("/api/session/{session_id}")
async def get_session(
    session_id: str,
    _: None = Depends(verify_api_key),
) -> dict[str, str | int | bool | None]:
    session = await session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "sessionId": session.session_id,
        "scamDetected": session.scam_detected,
        "totalMessagesExchanged": session.total_messages,
        "phase": session.phase,
        "completed": session.completed,
    }