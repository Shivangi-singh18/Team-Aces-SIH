"""Unified Medical Document Digitization Pipeline (Module B - MediKiosk).

Provides end-to-end integration:
Raw Image (file/bytes/base64) -> Preprocessing -> Dual OCR Engine -> Clinical Entity Extractor -> MedicalDocumentSchema.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .entity_extractor import extract_clinical_entities
from .image_preprocessor import ImageInput
from .ocr_engine import extract_raw_text
from .schemas import MedicalDocumentSchema

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Encapsulates the full result of the document digitization process."""

    raw_text: str
    entities: MedicalDocumentSchema
    ocr_engine: str
    llm_provider: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary containing structured entities and raw OCR text."""
        d = self.entities.to_dict()
        d["raw_ocr_text"] = self.raw_text
        return d

    def to_json(self, indent: int = 2) -> str:
        """Convert result to formatted JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=indent)


def process_medical_document(
    image_input: ImageInput,
    ocr_engine: str = "auto",
    llm_provider: str = "auto",
    preprocess: bool = True,
) -> MedicalDocumentSchema:
    """End-to-end processing: Ingests medical image and outputs structured MedicalDocumentSchema.

    Args:
        image_input: File path (str/Path), base64 string, bytes stream, or PIL Image.
        ocr_engine: 'auto', 'printed', 'handwritten', 'gcv', 'azure', 'trocr', 'easyocr'.
        llm_provider: 'auto', 'gemini', 'openai', 'heuristic'.
        preprocess: Apply medical document contrast/orientation preprocessing.

    Returns:
        Structured MedicalDocumentSchema conforming strictly to the MediKiosk contract.
    """
    logger.info(f"Digitizing document (ocr_engine={ocr_engine}, llm_provider={llm_provider})...")

    # 1. OCR text extraction
    raw_text = extract_raw_text(
        image_input=image_input,
        engine=ocr_engine,
        preprocess=preprocess,
    )

    # 2. Clinical entity extraction & structuring
    entities = extract_clinical_entities(
        raw_text=raw_text,
        provider=llm_provider,
    )

    return entities


def process_medical_document_full(
    image_input: ImageInput,
    ocr_engine: str = "auto",
    llm_provider: str = "auto",
    preprocess: bool = True,
) -> PipelineResult:
    """End-to-end processing returning both raw OCR text and structured clinical entities."""
    raw_text = extract_raw_text(
        image_input=image_input,
        engine=ocr_engine,
        preprocess=preprocess,
    )
    entities = extract_clinical_entities(
        raw_text=raw_text,
        provider=llm_provider,
    )
    return PipelineResult(
        raw_text=raw_text,
        entities=entities,
        ocr_engine=ocr_engine,
        llm_provider=llm_provider,
    )
