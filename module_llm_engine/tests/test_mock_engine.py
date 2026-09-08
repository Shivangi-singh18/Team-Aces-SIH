"""Unit tests for the Zero-API-Key Offline Mock clinical triage engine."""

import unittest
from module_llm_engine.mock_engine import ZeroApiKeyMockEngine
from module_llm_engine.schemas import LLMProcessingRequest


class TestMockEngine(unittest.TestCase):
    """Test suite verifying offline mock engine behaviors, triage logic, and contract compliance."""

    def setUp(self):
        self.engine = ZeroApiKeyMockEngine()

    def test_combined_voice_and_ocr(self):
        """Test processing of combined voice transcript + digitized OCR prescription."""
        req = LLMProcessingRequest(
            voice_transcript="I have severe chest pain and breathlessness since morning.",
            ocr_data={
                "document_type": "prescription",
                "diagnoses": ["Hypertension"],
                "medications": [
                    {"drug_name": "Amlodipine", "dosage": "5mg", "frequency": "1-0-0", "duration": "30 days"}
                ],
                "lab_results": [],
                "unparsed_text": "BP: 160/100 mmHg",
            },
            patient_demographics={"age": 58, "gender": "Female", "known_allergies": []},
        )

        resp = self.engine.process(req)

        # Assert contract types
        self.assertIsInstance(resp.chief_complaints, list)
        self.assertGreater(len(resp.chief_complaints), 0)
        self.assertIsInstance(resp.patient_symptoms, list)
        self.assertGreater(len(resp.patient_symptoms), 0)
        self.assertIsInstance(resp.icd10_codes, list)
        self.assertGreater(len(resp.icd10_codes), 0)

        # Assert clinical synthesis
        self.assertIn("Amlodipine", resp.medical_history_summary)
        self.assertIn("Hypertension", resp.medical_history_summary)

        # Assert risk stratification (chest pain + breathlessness should yield High or Critical risk)
        self.assertIn(resp.risk_assessment.risk_level, ["High", "Critical"])
        self.assertGreaterEqual(resp.risk_assessment.score, 7)
        self.assertEqual(resp.risk_assessment.recommended_specialty, "Cardiology")
        self.assertGreater(len(resp.risk_assessment.red_flags), 0)
        self.assertIn("Cardiology", resp.patient_friendly_instructions)

    def test_partial_input_voice_only(self):
        """Test processing when only voice transcript is provided (no OCR, no demographics)."""
        req = LLMProcessingRequest(
            voice_transcript="I have a high fever with chills and a very bad cough.",
            ocr_data=None,
            patient_demographics=None,
        )

        resp = self.engine.process(req)

        self.assertGreater(len(resp.chief_complaints), 0)
        # Check ICD-10 presence (Fever R50.9 or Cough/URI J06.9)
        codes = [item.code for item in resp.icd10_codes]
        self.assertTrue(any(c in ["R50.9", "J06.9"] for c in codes))
        self.assertEqual(resp.risk_assessment.recommended_specialty, "General Medicine")
        self.assertIn(resp.risk_assessment.risk_level, ["Medium", "Low"])
        self.assertTrue(len(resp.patient_friendly_instructions) > 20)

    def test_partial_input_ocr_only(self):
        """Test processing when only digitized OCR report is provided (no voice transcript)."""
        req = LLMProcessingRequest(
            voice_transcript=None,
            ocr_data={
                "document_type": "lab_report",
                "diagnoses": ["Type 2 Diabetes Mellitus"],
                "medications": [],
                "lab_results": [
                    {"test_name": "Fasting Blood Sugar", "value": "320", "unit": "mg/dL", "is_abnormal": True},
                    {"test_name": "Serum Creatinine", "value": "2.4", "unit": "mg/dL", "is_abnormal": True},
                ],
                "unparsed_text": "",
            },
            patient_demographics={"age": 62, "gender": "Male"},
        )

        resp = self.engine.process(req)

        # Abnormal labs (>250 glucose, >2.0 creatinine) should escalate risk
        self.assertGreaterEqual(resp.risk_assessment.score, 7)
        self.assertIn(resp.risk_assessment.risk_level, ["High", "Critical"])
        self.assertGreater(len(resp.risk_assessment.red_flags), 0)
        self.assertTrue(any("Hyperglycemia" in rf or "Creatinine" in rf for rf in resp.risk_assessment.red_flags))
        self.assertIn("Fasting Blood Sugar", resp.medical_history_summary)

    def test_allergy_contraindication_alert(self):
        """Test cross-checking of patient allergies against prescription medications."""
        req = LLMProcessingRequest(
            voice_transcript="I have a sore throat.",
            ocr_data={
                "document_type": "prescription",
                "diagnoses": ["Pharyngitis"],
                "medications": [
                    {"drug_name": "Amoxicillin", "dosage": "500mg", "frequency": "TDS", "duration": "5 days"}
                ],
                "lab_results": [],
            },
            patient_demographics={"age": 30, "gender": "Female", "known_allergies": ["Penicillin"]},
        )

        resp = self.engine.process(req)

        # Should flag penicillin cross-reactivity with amoxicillin
        self.assertTrue(
            any("ALLERGY CONTRAINDICATION" in rf for rf in resp.risk_assessment.red_flags),
            "Expected allergy contraindication red flag for Penicillin allergy vs Amoxicillin prescription",
        )
        self.assertEqual(resp.risk_assessment.risk_level, "Critical")
        self.assertEqual(resp.risk_assessment.score, 9)

    def test_sparse_input_fallback(self):
        """Test engine stability when empty/blank inputs are supplied."""
        req = LLMProcessingRequest(voice_transcript="", ocr_data={}, patient_demographics={})
        resp = self.engine.process(req)

        self.assertIsNotNone(resp)
        self.assertGreater(len(resp.chief_complaints), 0)
        self.assertEqual(resp.risk_assessment.risk_level, "Low")
        self.assertTrue(len(resp.patient_friendly_instructions) > 10)


if __name__ == "__main__":
    unittest.main()
