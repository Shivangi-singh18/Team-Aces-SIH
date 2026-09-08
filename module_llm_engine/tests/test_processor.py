"""Unit tests for ClinicalLLMEngine multi-tier fallback orchestration."""

import asyncio
import unittest
from unittest.mock import patch

from module_llm_engine.config import config
from module_llm_engine.llm_processor import ClinicalLLMEngine
from module_llm_engine.schemas import LLMProcessingRequest


class TestLLMProcessor(unittest.TestCase):
    """Test suite for ClinicalLLMEngine provider fallback and offline resilience."""

    def setUp(self):
        self.engine = ClinicalLLMEngine()

    def test_offline_fallback_when_keys_omitted(self):
        """Verify automatic zero-key fallback to mock engine when API keys are absent."""
        with patch.object(config, "GEMINI_API_KEY", None), \
             patch.object(config, "OPENAI_API_KEY", None), \
             patch.object(config, "FORCE_MOCK_MODE", False):

            req = LLMProcessingRequest(
                voice_transcript="I have severe chest pain and chest tightness since morning.",
                ocr_data=None,
                patient_demographics={"age": 50, "gender": "Male"},
            )

            resp = self.engine.process(req)

            self.assertEqual(resp.provider_used, "mock_offline")
            self.assertGreater(resp.processing_time_ms, 0)
            self.assertEqual(resp.risk_assessment.recommended_specialty, "Cardiology")
            self.assertIn(resp.risk_assessment.risk_level, ["High", "Critical"])

    def test_gemini_failure_falls_back_to_openai(self):
        """Simulate Gemini failure falling back to OpenAI."""
        mock_openai_resp = {
            "chief_complaints": ["Acute Bronchitis"],
            "patient_symptoms": ["Productive cough", "Wheezing"],
            "medical_history_summary": "Patient presenting with acute bronchitis.",
            "icd10_codes": [{"code": "J20.9", "description": "Acute bronchitis, unspecified"}],
            "risk_assessment": {
                "risk_level": "Medium",
                "score": 5,
                "red_flags": [],
                "recommended_specialty": "Pulmonology",
            },
            "patient_friendly_instructions": "Please wait in the Pulmonology consultation area.",
        }

        with patch.object(config, "GEMINI_API_KEY", "fake-gemini-key"), \
             patch.object(config, "OPENAI_API_KEY", "fake-openai-key"), \
             patch.object(config, "FORCE_MOCK_MODE", False), \
             patch.object(self.engine, "_call_gemini", return_value=None), \
             patch.object(self.engine, "_call_openai", return_value=mock_openai_resp):

            req = LLMProcessingRequest(voice_transcript="Wheezing and bad cough for 4 days.")
            resp = self.engine.process(req)

            self.assertTrue(resp.provider_used.startswith("openai:"))
            self.assertEqual(resp.chief_complaints, ["Acute Bronchitis"])
            self.assertEqual(resp.risk_assessment.recommended_specialty, "Pulmonology")

    def test_dual_failure_falls_back_to_mock(self):
        """Simulate both Gemini and OpenAI failing, guaranteeing mock fallback."""
        with patch.object(config, "GEMINI_API_KEY", "fake-gemini-key"), \
             patch.object(config, "OPENAI_API_KEY", "fake-openai-key"), \
             patch.object(config, "FORCE_MOCK_MODE", False), \
             patch.object(self.engine, "_call_gemini", side_effect=Exception("Gemini 500 error")), \
             patch.object(self.engine, "_call_openai", side_effect=Exception("OpenAI rate limit")):

            req = LLMProcessingRequest(voice_transcript="Severe fever and shivering.")
            resp = self.engine.process(req)

            self.assertEqual(resp.provider_used, "mock_offline")
            self.assertIn("General Medicine", resp.risk_assessment.recommended_specialty)
            self.assertIsNotNone(resp.patient_friendly_instructions)

    def test_async_process(self):
        """Verify asynchronous invocation via aprocess()."""
        req = LLMProcessingRequest(voice_transcript="Mild headache and dizziness.")
        loop = asyncio.new_event_loop()
        try:
            resp = loop.run_until_complete(self.engine.aprocess(req))
            self.assertIsNotNone(resp)
            self.assertEqual(resp.provider_used, "mock_offline")
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
