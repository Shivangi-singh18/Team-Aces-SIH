"""Unit tests for ImagePreprocessor."""

import base64
import io
import unittest
from PIL import Image

from module_b_ocr.image_preprocessor import ImagePreprocessor


class TestImagePreprocessor(unittest.TestCase):
    def setUp(self):
        # Create a small RGB test image
        self.img = Image.new("RGB", (200, 300), color=(255, 128, 64))

    def test_load_from_pil(self):
        loaded = ImagePreprocessor.load_image(self.img)
        self.assertEqual(loaded.size, (200, 300))
        self.assertEqual(loaded.mode, "RGB")

    def test_load_from_bytes(self):
        buf = io.BytesIO()
        self.img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        loaded = ImagePreprocessor.load_image(raw_bytes)
        self.assertEqual(loaded.size, (200, 300))

    def test_load_from_bytesio(self):
        buf = io.BytesIO()
        self.img.save(buf, format="JPEG")
        buf.seek(0)

        loaded = ImagePreprocessor.load_image(buf)
        self.assertEqual(loaded.size, (200, 300))

    def test_load_from_base64(self):
        buf = io.BytesIO()
        self.img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"

        loaded = ImagePreprocessor.load_image(data_uri)
        self.assertEqual(loaded.size, (200, 300))

    def test_preprocess_for_ocr(self):
        preprocessed = ImagePreprocessor.preprocess_for_ocr(
            self.img,
            grayscale=True,
            enhance_contrast=True,
            sharpen=True,
            max_dimension=150,
        )
        self.assertEqual(preprocessed.mode, "L")
        # Check downscaling
        self.assertLessEqual(max(preprocessed.size), 150)

    def test_binarize(self):
        binary = ImagePreprocessor.binarize(self.img, threshold=128)
        self.assertEqual(binary.mode, "1")


if __name__ == "__main__":
    unittest.main()
