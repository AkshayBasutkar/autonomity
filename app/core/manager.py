from __future__ import annotations

from datetime import datetime, timezone

from app.agent.agent import agent
from app.config.settings import settings
from app.detection.scam_detector import detect_scam
from app.intelligence.extractor import extract_intelligence
from app.models.schemas import (
    ConversationEntry,
    EngagementMetrics,
    ExtractedIntelligence,
    MessageRequest,
    MessageResponse,
    SessionState,
)
from app.services.guvi_callback import send_final_result
from app.services.session_store import session_store


def _merge_intelligence(existing: ExtractedIntelligence, new: ExtractedIntelligence) -> ExtractedIntelligence:
    return ExtractedIntelligence(
        bankAccounts=list({*existing.bankAccounts, *new.bankAccounts}),
        upiIds=list({*existing.upiIds, *new.upiIds}),
        phishingLinks=list({*existing.phishingLinks, *new.phishingLinks}),
        phoneNumbers=list({*existing.phoneNumbers, *new.phoneNumbers}),
        suspiciousKeywords=list({*existing.suspiciousKeywords, *new.suspiciousKeywords}),
    )


def _should_complete(session: SessionState) -> bool:
    if session.completed:
        return True
    if session.total_messages >= settings.max_messages_per_session:
        return True
    if session.scam_detected and session.phase == "exit" and session.total_messages >= 8:
        return True
    return False


async def handle_message(request: MessageRequest) -> MessageResponse:
    now = datetime.now(timezone.utc)
    session = await session_store.get(request.sessionId)
    if not session:
        session = SessionState(
            session_id=request.sessionId,
            created_at=now,
            last_updated_at=now,
        )
        for entry in request.conversationHistory:
            session.conversation.append(entry)

    latest_entry = ConversationEntry(
        sender=request.message.sender,
        text=request.message.text,
        timestamp=request.message.timestamp,
    )
    session.conversation.append(latest_entry)
    session.total_messages = len(session.conversation)

    detection = detect_scam(request.message.text)
    session.scam_score = max(session.scam_score, detection.score)
    if detection.scam_type and not session.scam_type:
        session.scam_type = detection.scam_type

    if session.scam_score >= settings.scam_score_threshold:
        session.scam_detected = True

    extracted = extract_intelligence(session.conversation)
    session.intelligence = _merge_intelligence(session.intelligence, extracted)

    agent_response_text = None
    if session.scam_detected:
        agent_response_text = agent.generate_response(session, latest_entry)
        session.conversation.append(
            ConversationEntry(
                sender="user",
                text=agent_response_text,
                timestamp=now,
            )
        )
        session.total_messages = len(session.conversation)
        session.agent_notes = "Scammer used urgency or sensitive info request patterns."

    session.last_updated_at = now
    session.completed = _should_complete(session)

    await session_store.set(session)

    if session.completed and session.scam_detected:
        await send_final_result(session)

    duration = int((now - session.created_at).total_seconds())
    response = MessageResponse(
        scamDetected=session.scam_detected,
        engagementMetrics=EngagementMetrics(
            engagementDurationSeconds=duration,
            totalMessagesExchanged=session.total_messages,
        ),
        extractedIntelligence=session.intelligence,
        agentNotes=session.agent_notes,
        agentResponse=agent_response_text,
    )
    return response