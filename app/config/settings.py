from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_secret_key: str = "CHANGE_ME"
    groq_api_key: str | None = None
    model_name: str = "llama-3.1-70b-versatile"

    redis_url: str | None = None
    guvi_callback_url: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

    log_level: str = "INFO"
    session_ttl_seconds: int = 24 * 60 * 60
    max_messages_per_session: int = 25
    scam_score_threshold: int = 70
    llm_detection_enabled: bool = True
    llm_weight: int = 40


settings = Settings()
