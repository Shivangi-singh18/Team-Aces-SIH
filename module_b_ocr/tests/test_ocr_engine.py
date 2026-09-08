"""Unit tests for DualOCREngine."""

import unittest
from unittest.mock import MagicMock
from PIL import Image

from module_b_ocr.ocr_engine import (
    DualOCREngine,
    FallbackMockEngine,
    extract_raw_text,
)


class TestOCREngine(unittest.TestCase):
    def setUp(self):
        self.img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        self.dual_engine = DualOCREngine()

    def test_fallback_engine(self):
        fallback = FallbackMockEngine()
        self.assertTrue(fallback.is_available())
        text = fallback.extract_text(self.img)
        self.assertIn("OCR Fallback Note", text)

    def test_auto_fallback_when_no_credentials(self):
        # In a test environment without GCV / Azure keys or local models,
        # auto mode should gracefully fall back without raising an unhandled crash
        text = extract_raw_text(self.img, engine="auto")
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)

    def test_mocked_gcv_engine(self):
        mock_gcv = MagicMock()
        mock_gcv.is_available.return_value = True
        mock_gcv.extract_text.return_value = "Dr. Mehta Clinic\nTab. Paracetamol 500mg"

        engine = DualOCREngine()
        engine.gcv = mock_gcv

        text = engine.extract(self.img, engine="gcv")
        self.assertIn("Tab. Paracetamol 500mg", text)
        mock_gcv.extract_text.assert_called_once()

    def test_mocked_handwritten_engine(self):
        mock_trocr = MagicMock()
        mock_trocr.is_available.return_value = True
        mock_trocr.extract_text.return_value = "Handwritten Rx: Augmentin 625mg"

        engine = DualOCREngine()
        engine.trocr = mock_trocr

        text = engine.extract(self.img, engine="trocr")
        self.assertEqual(text, "Handwritten Rx: Augmentin 625mg")


if __name__ == "__main__":
    unittest.main()
