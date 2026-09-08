"""MediKiosk LLM Orchestration Engine - Dynamic Dual-LLM Core Engine.

Orchestrates Google Gemini as primary provider (structured JSON schema),
OpenAI (gpt-4o-mini) as secondary fallback, and Zero-API-Key Offline Mock Mode
as zero-dependency resilience guarantee.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Optional

from .config import config
from .mock_engine import ZeroApiKeyMockEngine, mock_engine
from .prompts import CLINICAL_SYSTEM_PROMPT, format_clinical_user_prompt
from .schemas import ClinicalLLMResponse, LLMProcessingRequest

logger = logging.getLogger("medikiosk.llm_processor")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class ClinicalLLMEngine:
    """Dynamic multi-tier clinical intelligence engine.

    Tier 1: Google Gemini (Structured Schema via google-genai)
    Tier 2: OpenAI gpt-4o-mini (JSON mode)
    Tier 3: Zero-API-Key Offline Mock Mode (Zero network/credentials required)
    """

    def __init__(self, mock_fallback: Optional[ZeroApiKeyMockEngine] = None):
        self.mock_engine = mock_fallback or mock_engine
        self._gemini_client = None
        self._openai_client = None

    def _get_gemini_client(self):
        """Lazy initialization of Google GenAI client."""
        if self._gemini_client is None and config.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                logger.info("Initialized Google Gemini client.")
            except Exception as exc:
                logger.warning("Failed to initialize Google Gemini client: %s", exc)
                self._gemini_client = False
        return self._gemini_client if self._gemini_client else None

    def _get_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._openai_client is None and config.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("Initialized OpenAI client.")
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI client: %s", exc)
                self._openai_client = False
        return self._openai_client if self._openai_client else None

    @staticmethod
    def _clean_json_text(raw_text: str) -> str:
        """Strip markdown code blocks or wrapping quotes from raw LLM output."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Attempt inference using Google Gemini."""
        client = self._get_gemini_client()
        if not client:
            return None

        try:
            from google.genai import types

            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=CLINICAL_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw_text = response.text or ""
            cleaned = self._clean_json_text(raw_text)
            return json.loads(cleaned)
        except Exception as exc:
            logger.warning("Gemini inference failed: %s. Proceeding to fallback.", exc)
            return None

    def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Attempt inference using OpenAI gpt-4o-mini."""
        client = self._get_openai_client()
        if not client:
            return None

        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": CLINICAL_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw_content = response.choices[0].message.content or ""
            cleaned = self._clean_json_text(raw_content)
            return json.loads(cleaned)
        except Exception as exc:
            logger.warning("OpenAI inference failed: %s. Proceeding to fallback.", exc)
            return None

    def process(self, request: LLMProcessingRequest) -> ClinicalLLMResponse:
        """Process clinical input across dynamic tiers with guaranteed schema compliance."""
        start_time = time.perf_counter()
        user_prompt = format_clinical_user_prompt(request)

        # Tier 0: Forced Mock Mode
        if config.FORCE_MOCK_MODE:
            logger.info("MEDIKIOSK_MOCK_MODE active - routing directly to ZeroApiKeyMockEngine.")
            resp = self.mock_engine.process(request)
            resp.processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return resp

        # Tier 1: Google Gemini
        if config.is_gemini_configured():
            logger.info("Attempting inference via Google Gemini (%s)...", config.GEMINI_MODEL)
            try:
                data = self._call_gemini(user_prompt)
                if data:
                    resp = ClinicalLLMResponse.model_validate(data)
                    resp.provider_used = f"gemini:{config.GEMINI_MODEL}"
                    resp.processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    logger.info("Gemini inference succeeded in %sms.", resp.processing_time_ms)
                    return resp
            except Exception as exc:
                logger.warning("Gemini processing step encountered error: %s", exc)

        # Tier 2: OpenAI gpt-4o-mini
        if config.is_openai_configured():
            logger.info("Attempting inference via OpenAI (%s)...", config.OPENAI_MODEL)
            try:
                data = self._call_openai(user_prompt)
                if data:
                    resp = ClinicalLLMResponse.model_validate(data)
                    resp.provider_used = f"openai:{config.OPENAI_MODEL}"
                    resp.processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    logger.info("OpenAI inference succeeded in %sms.", resp.processing_time_ms)
                    return resp
            except Exception as exc:
                logger.warning("OpenAI processing step encountered error: %s", exc)

        # Tier 3: Zero-API-Key Offline Mock Mode
        logger.info("Routing to Zero-API-Key Offline Mock Engine.")
        resp = self.mock_engine.process(request)
        resp.provider_used = "mock_offline"
        resp.processing_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return resp

    async def aprocess(self, request: LLMProcessingRequest) -> ClinicalLLMResponse:
        """Asynchronous entry point for FastAPI event loop execution."""
        import anyio
        return await anyio.to_thread.run_sync(self.process, request)


engine = ClinicalLLMEngine()
