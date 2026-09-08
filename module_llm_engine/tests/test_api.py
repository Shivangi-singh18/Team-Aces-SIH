"""Integration tests for the MediKiosk FastAPI microservice."""

import unittest
from fastapi.testclient import TestClient
from module_llm_engine.main import app


class TestAPIEndpoints(unittest.TestCase):
    """Test suite verifying FastAPI endpoints, CORS, and request handling."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        """GET /health must return 200 and service metadata."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "MediKiosk LLM Orchestration Engine")
        self.assertIn("active_provider", data)

    def test_providers_status(self):
        """GET /api/v1/llm/providers must return provider details."""
        response = self.client.get("/api/v1/llm/providers")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("preferred_provider", data)
        self.assertIn("providers", data)
        self.assertIn("mock_offline", data["providers"])

    def test_cors_headers(self):
        """Ensure permissive CORS allows cross-origin requests from mobile emulators."""
        response = self.client.options(
            "/api/v1/llm/process",
            headers={
                "Origin": "http://localhost:19006",  # React Native / Expo web
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        self.assertEqual(response.status_code, 200)
        # With allow_credentials=True, CORS reflects allowed requesting origin
        self.assertIn(
            response.headers.get("access-control-allow-origin"),
            ["*", "http://localhost:19006"],
        )

    def test_process_combined_payload(self):
        """POST /api/v1/llm/process with both voice transcript and OCR data."""
        payload = {
            "voice_transcript": "Severe radiating chest tightness and shortness of breath.",
            "ocr_data": {
                "document_type": "prescription",
                "diagnoses": ["Hypertension"],
                "medications": [
                    {"drug_name": "Amlodipine", "dosage": "5mg", "frequency": "OD", "duration": "30 days"}
                ],
                "lab_results": [],
                "unparsed_text": "BP 160/95",
            },
            "patient_demographics": {
                "age": 60,
                "gender": "Male",
                "known_allergies": ["Sulfa"],
            },
        }

        response = self.client.post("/api/v1/llm/process", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("chief_complaints", data)
        self.assertIn("patient_symptoms", data)
        self.assertIn("medical_history_summary", data)
        self.assertIn("icd10_codes", data)
        self.assertIn("risk_assessment", data)
        self.assertIn("patient_friendly_instructions", data)

        # Verify risk assessment fields
        risk = data["risk_assessment"]
        self.assertIn(risk["risk_level"], ["High", "Critical"])
        self.assertGreaterEqual(risk["score"], 7)
        self.assertEqual(risk["recommended_specialty"], "Cardiology")
        self.assertGreater(len(risk["red_flags"]), 0)

    def test_process_voice_only_payload(self):
        """POST /api/v1/llm/process with voice transcript only."""
        payload = {
            "voice_transcript": "I have been vomiting and have severe stomach cramps since last night."
        }

        response = self.client.post("/api/v1/llm/process", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertGreater(len(data["chief_complaints"]), 0)
        self.assertEqual(data["risk_assessment"]["recommended_specialty"], "Gastroenterology")

    def test_process_ocr_only_payload(self):
        """POST /api/v1/llm/process with OCR digitized report only."""
        payload = {
            "ocr_data": {
                "document_type": "lab_report",
                "diagnoses": ["Anemia"],
                "medications": [],
                "lab_results": [
                    {"test_name": "Hemoglobin", "value": "7.2", "unit": "g/dL", "is_abnormal": True}
                ],
                "unparsed_text": "",
            }
        }

        response = self.client.post("/api/v1/llm/process", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("Hemoglobin", data["medical_history_summary"])
        self.assertGreater(len(data["chief_complaints"]), 0)

    def test_invalid_payload_handling(self):
        """Ensure malformed JSON or invalid types return 422 Unprocessable Entity."""
        bad_payload = {
            "ocr_data": "invalid_string_instead_of_dict"
        }
        response = self.client.post("/api/v1/llm/process", json=bad_payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
