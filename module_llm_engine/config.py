"""MediKiosk LLM Orchestration Engine - Configuration & Environment Management."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()


class EngineConfig:
    """Central configuration for LLM Engine providers and microservice."""

    def __init__(self):
        # Google Gemini Settings
        self.GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # OpenAI Settings
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Mock & Fallback Settings
        # If MEDIKIOSK_MOCK_MODE is "1" or "true", mock mode is forced regardless of keys
        self.FORCE_MOCK_MODE: bool = os.getenv("MEDIKIOSK_MOCK_MODE", "false").lower() in ("1", "true", "yes")

        # Server Settings
        self.HOST: str = os.getenv("MEDIKIOSK_HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("MEDIKIOSK_PORT", "8000"))

    def is_gemini_configured(self) -> bool:
        """Check if Gemini credentials are present and not forced to mock."""
        return bool(self.GEMINI_API_KEY and not self.FORCE_MOCK_MODE)

    def is_openai_configured(self) -> bool:
        """Check if OpenAI credentials are present and not forced to mock."""
        return bool(self.OPENAI_API_KEY and not self.FORCE_MOCK_MODE)

    def get_preferred_provider(self) -> str:
        """Determine primary LLM provider based on current environment configuration."""
        if self.FORCE_MOCK_MODE:
            return "mock_offline"
        if self.is_gemini_configured():
            return f"gemini ({self.GEMINI_MODEL})"
        if self.is_openai_configured():
            return f"openai ({self.OPENAI_MODEL})"
        return "mock_offline"


config = EngineConfig()
