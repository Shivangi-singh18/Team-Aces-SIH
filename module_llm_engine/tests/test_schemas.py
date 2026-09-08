"""Unit tests for Pydantic v2 schemas and validation rules."""

import unittest
from pydantic import ValidationError
from module_llm_engine.schemas import (
    ClinicalLLMResponse,
    ICD10Code,
    LLMProcessingRequest,
    RiskAssessment,
)


class TestSchemas(unittest.TestCase):
    """Test suite for data contracts and validation constraints."""

    def test_valid_llm_processing_request_full(self):
        req = LLMProcessingRequest(
            voice_transcript="Patient reports sharp chest pain radiating to left shoulder.",
            ocr_data={
                "document_type": "prescription",
                "diagnoses": ["Hypertension"],
                "medications": [{"drug_name": "Amlodipine", "dosage": "5mg", "frequency": "OD", "duration": "10d"}],
                "lab_results": [],
            },
            patient_demographics={"age": 52, "gender": "Male", "known_allergies": ["Penicillin"]},
        )
        self.assertTrue(req.has_content())
        self.assertIn("chest pain", req.voice_transcript)
        self.assertEqual(req.patient_demographics["age"], 52)

    def test_valid_llm_processing_request_partial(self):
        voice_only = LLMProcessingRequest(voice_transcript="Persistent cough and fever.")
        self.assertTrue(voice_only.has_content())
        self.assertIsNone(voice_only.ocr_data)
        self.assertIsNone(voice_only.patient_demographics)

        ocr_only = LLMProcessingRequest(
            ocr_data={"document_type": "lab_report", "lab_results": [{"test_name": "Hb", "value": "9.5", "unit": "g/dL", "is_abnormal": True}]}
        )
        self.assertTrue(ocr_only.has_content())
        self.assertIsNone(ocr_only.voice_transcript)

        empty_req = LLMProcessingRequest()
        self.assertFalse(empty_req.has_content())

    def test_risk_assessment_validation(self):
        valid_risk = RiskAssessment(
            risk_level="High",
            score=8,
            red_flags=["Suspected acute coronary syndrome"],
            recommended_specialty="Cardiology",
        )
        self.assertEqual(valid_risk.score, 8)
        self.assertEqual(valid_risk.risk_level, "High")

        # Invalid score > 10
        with self.assertRaises(ValidationError):
            RiskAssessment(
                risk_level="High",
                score=11,
                red_flags=[],
                recommended_specialty="Cardiology",
            )

        # Invalid score < 1
        with self.assertRaises(ValidationError):
            RiskAssessment(
                risk_level="Low",
                score=0,
                red_flags=[],
                recommended_specialty="General Medicine",
            )

        # Invalid risk_level
        with self.assertRaises(ValidationError):
            RiskAssessment(
                risk_level="SuperCritical",  # type: ignore
                score=9,
                red_flags=[],
                recommended_specialty="Cardiology",
            )

    def test_clinical_response_serialization(self):
        resp = ClinicalLLMResponse(
            chief_complaints=["Acute chest pain"],
            patient_symptoms=["Precordial pain", "Shortness of breath"],
            medical_history_summary="Patient presenting with acute chest discomfort.",
            icd10_codes=[ICD10Code(code="R07.9", description="Chest pain, unspecified")],
            risk_assessment=RiskAssessment(
                risk_level="High",
                score=8,
                red_flags=["Potential cardiac event"],
                recommended_specialty="Cardiology",
            ),
            patient_friendly_instructions="Please report to the nearest nurse immediately.",
            provider_used="mock_offline",
            processing_time_ms=12.5,
        )

        dumped = resp.model_dump()
        self.assertEqual(dumped["risk_assessment"]["score"], 8)
        self.assertEqual(len(dumped["icd10_codes"]), 1)
        self.assertEqual(dumped["icd10_codes"][0]["code"], "R07.9")

        # Roundtrip JSON test
        json_str = resp.model_dump_json()
        restored = ClinicalLLMResponse.model_validate_json(json_str)
        self.assertEqual(restored.chief_complaints, ["Acute chest pain"])
        self.assertEqual(restored.risk_assessment.risk_level, "High")


if __name__ == "__main__":
    unittest.main()
