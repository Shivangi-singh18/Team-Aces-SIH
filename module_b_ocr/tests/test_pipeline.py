"""Unit and integration tests for the unified Module B pipeline."""

import unittest
from unittest.mock import MagicMock, patch
from PIL import Image

from module_b_ocr.pipeline import (
    process_medical_document,
    process_medical_document_full,
)
from module_b_ocr.schemas import MedicalDocumentSchema


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (200, 200), color=(255, 255, 255))

    @patch("module_b_ocr.pipeline.extract_raw_text")
    def test_pipeline_with_mocked_ocr(self, mock_ocr):
        mock_ocr.return_value = """
        Dr. Sharma OPD Clinic
        Dx: Viral Fever
        Rx:
        Tab. Paracetamol 500mg 1-0-1 3 days
        """

        result = process_medical_document(self.img, ocr_engine="auto", llm_provider="heuristic")
        self.assertIsInstance(result, MedicalDocumentSchema)
        self.assertEqual(result.document_type, "prescription")
        self.assertTrue(len(result.medications) >= 1)
        self.assertEqual(result.medications[0].drug_name.lower(), "paracetamol")

    @patch("module_b_ocr.pipeline.extract_raw_text")
    def test_pipeline_full_result(self, mock_ocr):
        mock_ocr.return_value = "Test Document Text"
        full_res = process_medical_document_full(self.img)

        self.assertEqual(full_res.raw_text, "Test Document Text")
        self.assertIsInstance(full_res.entities, MedicalDocumentSchema)
        d = full_res.to_dict()
        self.assertIn("raw_ocr_text", d)
        self.assertIn("document_type", d)

        json_out = full_res.to_json()
        self.assertIn('"raw_ocr_text"', json_out)


if __name__ == "__main__":
    unittest.main()
