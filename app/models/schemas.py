from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, AliasChoices


class Message(BaseModel):
    sender: Literal["scammer", "user"]
    text: str
    timestamp: datetime


class ConversationEntry(BaseModel):
    sender: Literal["scammer", "user"] | None = None
    text: str
    timestamp: datetime


class Metadata(BaseModel):
    channel: str | None = None
    language: str | None = None
    locale: str | None = None


class MessageRequest(BaseModel):
    sessionId: str = Field(..., validation_alias=AliasChoices("sessionId", "sessionld"))
    message: Message
    conversationHistory: list[ConversationEntry] = Field(default_factory=list)
    metadata: Metadata | None = None

    model_config = {
        "populate_by_name": True,
    }


class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int
    totalMessagesExchanged: int


class ExtractedIntelligence(BaseModel):
    bankAccounts: list[str] = Field(default_factory=list)
    upiIds: list[str] = Field(default_factory=list)
    phishingLinks: list[str] = Field(default_factory=list)
    phoneNumbers: list[str] = Field(default_factory=list)
    suspiciousKeywords: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    status: str = "success"
    scamDetected: bool
    engagementMetrics: EngagementMetrics
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str = ""
    agentResponse: str | None = None


class SessionState(BaseModel):
    session_id: str
    created_at: datetime
    last_updated_at: datetime
    total_messages: int = 0
    scam_detected: bool = False
    scam_score: int = 0
    scam_type: str | None = None
    persona: str | None = None
    phase: str = "init"
    conversation: list[ConversationEntry] = Field(default_factory=list)
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    agent_notes: str = ""
    completed: bool = False
    persona_memory: dict[str, list[str]] = Field(default_factory=dict)
