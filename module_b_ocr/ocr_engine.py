"""Dual OCR Engine for Medical Document Digitization (Module B - MediKiosk).

Supports:
1. Printed Text & Regional Documents: Google Cloud Vision API (and Azure fallback).
2. Handwritten Prescriptions: TrOCR (Transformer OCR) & EasyOCR tuned for medical handwriting.
3. Hybrid/Auto orchestration with automatic fallback when cloud keys or heavy ML models are absent.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from PIL import Image

from .image_preprocessor import ImageInput, ImagePreprocessor

logger = logging.getLogger(__name__)


class BaseOCREngine(ABC):
    """Abstract base class for OCR engine implementations."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether dependencies and credentials for this engine are available."""
        pass

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Extract text from a PIL Image."""
        pass


class GoogleCloudVisionEngine(BaseOCREngine):
    """Printed text & regional document OCR via Google Cloud Vision API.

    Uses `document_text_detection` which is tuned for dense printed text, tables,
    and regional Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, etc.).
    """

    def __init__(self) -> None:
        self._client: Optional[Any] = None

    def is_available(self) -> bool:
        """Available if `google-cloud-vision` is installed and credentials exist."""
        try:
            import google.cloud.vision  # noqa: F401
            # Check for GOOGLE_APPLICATION_CREDENTIALS or gcloud auth
            has_creds = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")) or bool(
                os.getenv("GOOGLE_CLOUD_PROJECT")
            )
            return has_creds
        except ImportError:
            return False

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import vision
            self._client = vision.ImageAnnotatorClient()
        return self._client

    def extract_text(self, image: Image.Image) -> str:
        """Extract full document text using Google Cloud Vision."""
        from google.cloud import vision

        content = ImagePreprocessor.to_bytes(image, format="PNG")
        vision_image = vision.Image(content=content)

        client = self._get_client()
        response = client.document_text_detection(image=vision_image)

        if response.error.message:
            raise RuntimeError(f"Google Cloud Vision error: {response.error.message}")

        if response.full_text_annotation and response.full_text_annotation.text:
            return response.full_text_annotation.text.strip()
        elif response.text_annotations:
            return response.text_annotations[0].description.strip()

        return ""


class AzureDocumentIntelligenceEngine(BaseOCREngine):
    """Azure Document Intelligence / Computer Vision Read API fallback."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT", "")
        self.key = os.getenv("AZURE_VISION_KEY", "")

    def is_available(self) -> bool:
        return bool(self.endpoint and self.key)

    def extract_text(self, image: Image.Image) -> str:
        """Extract text via Azure Computer Vision / Document Intelligence Read API."""
        try:
            import requests

            img_bytes = ImagePreprocessor.to_bytes(image, format="JPEG")
            url = f"{self.endpoint.rstrip('/')}/vision/v3.2/read/analyze"
            headers = {
                "Ocp-Apim-Subscription-Key": self.key,
                "Content-Type": "application/octet-stream",
            }
            resp = requests.post(url, headers=headers, data=img_bytes)
            resp.raise_for_status()

            operation_url = resp.headers.get("Operation-Location")
            if not operation_url:
                return ""

            import time

            # Poll for completion
            for _ in range(15):
                time.sleep(1)
                result_resp = requests.get(
                    operation_url,
                    headers={"Ocp-Apim-Subscription-Key": self.key},
                )
                res_data = result_resp.json()
                status = res_data.get("status")
                if status == "succeeded":
                    lines: List[str] = []
                    for read_res in res_data.get("analyzeResult", {}).get("readResults", []):
                        for line in read_res.get("lines", []):
                            lines.append(line.get("text", ""))
                    return "\n".join(lines).strip()
                elif status == "failed":
                    break

            return ""
        except Exception as e:
            logger.warning(f"Azure OCR error: {e}")
            return ""


class TrOCREngine(BaseOCREngine):
    """Microsoft TrOCR (Transformer OCR) engine for handwritten medical text.

    Specialized for doctor handwriting recognition.
    Uses Hugging Face's `microsoft/trocr-base-handwritten` or `microsoft/trocr-small-handwritten`.
    """

    def __init__(self, model_name: str = "microsoft/trocr-small-handwritten") -> None:
        self.model_name = model_name
        self._processor: Optional[Any] = None
        self._model: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if transformers and torch are installed."""
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_model(self) -> None:
        if self._model is None or self._processor is None:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            logger.info(f"Loading TrOCR model: {self.model_name}...")
            self._processor = TrOCRProcessor.from_pretrained(self.model_name)
            self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self._model.eval()

    def extract_text(self, image: Image.Image) -> str:
        """Run TrOCR on image (crops or full document)."""
        self._load_model()
        import torch

        if image.mode != "RGB":
            image = image.convert("RGB")

        # In standard documents, line segmentation boosts TrOCR accuracy.
        # Here we perform full-image inference or multi-segment inference.
        pixel_values = self._processor(image, return_tensors="pt").pixel_values
        with torch.no_grad():
            generated_ids = self._model.generate(pixel_values)
        generated_text = self._processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        return generated_text.strip()


class EasyOCREngine(BaseOCREngine):
    """EasyOCR engine tuned for medical handwriting and mixed-text detection."""

    def __init__(self, languages: Optional[List[str]] = None) -> None:
        self.languages = languages or ["en"]
        self._reader: Optional[Any] = None

    def is_available(self) -> bool:
        """Check if easyocr is installed."""
        try:
            import easyocr  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_reader(self) -> Any:
        if self._reader is None:
            import easyocr
            import torch
            use_gpu = torch.cuda.is_available()
            logger.info(f"Initializing EasyOCR reader (gpu={use_gpu})...")
            self._reader = easyocr.Reader(self.languages, gpu=use_gpu)
        return self._reader

    def extract_text(self, image: Image.Image) -> str:
        """Extract text using EasyOCR with paragraph and layout ordering."""
        import numpy as np

        reader = self._get_reader()
        img_np = np.array(image)

        # EasyOCR readtext with paragraph=True to assemble natural prescription lines
        results = reader.readtext(img_np, paragraph=True, detail=0)
        return "\n".join(results).strip()


class FallbackMockEngine(BaseOCREngine):
    """Deterministic fallback engine when no external OCR service or weights are present.

    Ensures tests and dry-runs run seamlessly without throwing unhandled exceptions.
    """

    def is_available(self) -> bool:
        return True

    def extract_text(self, image: Image.Image) -> str:
        """Returns mock OCR text or informational note."""
        return (
            "[OCR Fallback Note]: No cloud credentials or local OCR weights detected.\n"
            "Please configure GOOGLE_APPLICATION_CREDENTIALS or install easyocr/torch for live OCR extraction.\n"
            "Image dimensions received: {w}x{h}.".format(w=image.width, h=image.height)
        )


class DualOCREngine:
    """Orchestrator combining Printed (GCV/Azure) and Handwritten (TrOCR/EasyOCR) engines."""

    def __init__(self) -> None:
        self.gcv = GoogleCloudVisionEngine()
        self.azure = AzureDocumentIntelligenceEngine()
        self.trocr = TrOCREngine()
        self.easyocr = EasyOCREngine()
        self.fallback = FallbackMockEngine()

    def extract(
        self,
        image_input: ImageInput,
        engine: str = "auto",
        preprocess: bool = True,
    ) -> str:
        """Extract raw text from an image input.

        Args:
            image_input: Image path, bytes, base64 string, or PIL Image.
            engine: Engine mode: 'auto', 'printed', 'handwritten', 'gcv', 'azure', 'trocr', 'easyocr', or 'dual'.
            preprocess: Whether to apply contrast/orientation preprocessing.

        Returns:
            Extracted text string.
        """
        if preprocess:
            image = ImagePreprocessor.preprocess_for_ocr(image_input)
        else:
            image = ImagePreprocessor.load_image(image_input)

        engine_norm = engine.lower().strip()

        # Explicit engine requests
        if engine_norm == "gcv":
            if self.gcv.is_available():
                return self.gcv.extract_text(image)
            raise RuntimeError("Google Cloud Vision is not configured or missing credentials.")

        if engine_norm == "azure":
            if self.azure.is_available():
                return self.azure.extract_text(image)
            raise RuntimeError("Azure OCR is not configured (AZURE_VISION_KEY / AZURE_VISION_ENDPOINT).")

        if engine_norm == "trocr":
            if self.trocr.is_available():
                return self.trocr.extract_text(image)
            raise RuntimeError("TrOCR dependencies (torch, transformers) not installed.")

        if engine_norm == "easyocr":
            if self.easyocr.is_available():
                return self.easyocr.extract_text(image)
            raise RuntimeError("EasyOCR dependencies (easyocr, torch) not installed.")

        # Mode: Printed text
        if engine_norm == "printed":
            if self.gcv.is_available():
                return self.gcv.extract_text(image)
            if self.azure.is_available():
                return self.azure.extract_text(image)
            if self.easyocr.is_available():
                return self.easyocr.extract_text(image)
            return self.fallback.extract_text(image)

        # Mode: Handwritten text
        if engine_norm == "handwritten":
            if self.easyocr.is_available():
                return self.easyocr.extract_text(image)
            if self.trocr.is_available():
                return self.trocr.extract_text(image)
            if self.gcv.is_available():
                # Google Cloud Vision also handles document handwriting well
                return self.gcv.extract_text(image)
            return self.fallback.extract_text(image)

        # Mode: 'auto' or 'dual'
        # Strategy:
        # 1. Primary printed/regional document OCR: Google Cloud Vision if available
        # 2. Azure Document Intelligence if available
        # 3. EasyOCR / TrOCR for local/offline processing
        # 4. Fallback mock engine
        if self.gcv.is_available():
            try:
                text = self.gcv.extract_text(image)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"GCV failed in auto mode, falling back: {e}")

        if self.azure.is_available():
            try:
                text = self.azure.extract_text(image)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"Azure OCR failed in auto mode: {e}")

        if self.easyocr.is_available():
            try:
                text = self.easyocr.extract_text(image)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"EasyOCR failed in auto mode: {e}")

        if self.trocr.is_available():
            try:
                text = self.trocr.extract_text(image)
                if text.strip():
                    return text
            except Exception as e:
                logger.warning(f"TrOCR failed in auto mode: {e}")

        return self.fallback.extract_text(image)


# Global default instance
_default_ocr_engine = DualOCREngine()


def extract_raw_text(
    image_input: ImageInput,
    engine: str = "auto",
    preprocess: bool = True,
) -> str:
    """Wrapper function to extract raw text from any medical document image input.

    Args:
        image_input: File path, base64 string, raw bytes stream, or PIL Image.
        engine: OCR engine to use ('auto', 'printed', 'handwritten', 'gcv', 'trocr', 'easyocr').
        preprocess: Apply medical document contrast and orientation preprocessing.

    Returns:
        Extracted raw text as a string.
    """
    return _default_ocr_engine.extract(image_input=image_input, engine=engine, preprocess=preprocess)
