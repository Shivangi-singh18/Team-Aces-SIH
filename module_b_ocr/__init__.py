"""Module B - Medical Document Digitization (MediKiosk).

Provides dual OCR pipeline (printed + handwritten) and LLM-powered structured
clinical entity extraction for OPD prescriptions, lab reports, and discharge summaries.
"""

from .entity_extractor import (
    ClinicalEntityExtractor,
    GeminiEntityExtractor,
    HeuristicRuleBasedExtractor,
    OpenAIEntityExtractor,
    extract_clinical_entities,
)
from .image_preprocessor import ImageInput, ImagePreprocessor
from .ocr_engine import (
    AzureDocumentIntelligenceEngine,
    DualOCREngine,
    EasyOCREngine,
    GoogleCloudVisionEngine,
    TrOCREngine,
    extract_raw_text,
)
from .pipeline import (
    PipelineResult,
    process_medical_document,
    process_medical_document_full,
)
from .schemas import (
    DocumentType,
    LabResult,
    MedicalDocumentSchema,
    Medication,
)

__all__ = [
    # Schemas
    "DocumentType",
    "Medication",
    "LabResult",
    "MedicalDocumentSchema",
    # Preprocessor
    "ImageInput",
    "ImagePreprocessor",
    # OCR Engines
    "extract_raw_text",
    "DualOCREngine",
    "GoogleCloudVisionEngine",
    "AzureDocumentIntelligenceEngine",
    "TrOCREngine",
    "EasyOCREngine",
    # Entity Extraction
    "extract_clinical_entities",
    "ClinicalEntityExtractor",
    "GeminiEntityExtractor",
    "OpenAIEntityExtractor",
    "HeuristicRuleBasedExtractor",
    # End-to-end Pipeline
    "process_medical_document",
    "process_medical_document_full",
    "PipelineResult",
]

__version__ = "1.0.0"
