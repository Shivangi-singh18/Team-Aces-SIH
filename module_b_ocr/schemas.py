"""Medical Document Digitization Schemas (Module B - MediKiosk).

Defines strict Pydantic v2 schemas conforming to the MediKiosk data contract.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["prescription", "lab_report", "discharge_summary", "unknown"]


class Medication(BaseModel):
    """Structured clinical medication entity."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    drug_name: str = Field(
        ...,
        description="Name of the medicine (brand name or generic name, e.g. Paracetamol, Amoxicillin).",
    )
    dosage: str = Field(
        ...,
        description="Strength or dosage specification (e.g. 500mg, 10ml, 1 tab).",
    )
    frequency: str = Field(
        ...,
        description="Frequency of administration (e.g. 1-0-1, TDS, Once daily, SOS).",
    )
    duration: str = Field(
        ...,
        description="Duration of the treatment (e.g. 5 days, 1 month, 2 weeks).",
    )


class LabResult(BaseModel):
    """Structured diagnostic laboratory test result."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    test_name: str = Field(
        ...,
        description="Name of the medical test (e.g. Hemoglobin, Fasting Blood Sugar, Serum Creatinine).",
    )
    value: str = Field(
        ...,
        description="Observed numeric or categorical result value (e.g. 13.5, 120, Positive).",
    )
    unit: str = Field(
        ...,
        description="Measurement unit (e.g. g/dL, mg/dL, mmol/L, %).",
    )
    is_abnormal: bool = Field(
        ...,
        description="Flag indicating if the test value lies outside the normal reference range.",
    )


class MedicalDocumentSchema(BaseModel):
    """Root structured schema extracted from digitized medical documents."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    document_type: DocumentType = Field(
        default="unknown",
        description="Classification of the document type.",
    )
    diagnoses: List[str] = Field(
        default_factory=list,
        description="List of clinical impressions, preliminary/final diagnoses or symptoms.",
    )
    medications: List[Medication] = Field(
        default_factory=list,
        description="List of prescribed pharmaceutical drugs.",
    )
    lab_results: List[LabResult] = Field(
        default_factory=list,
        description="List of extracted laboratory or pathology parameters.",
    )
    unparsed_text: str = Field(
        default="",
        description="Any residual text or metadata (e.g. doctor notes, hospital headers) not cleanly classified.",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema instance to a standard Python dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Serialize schema to a formatted JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MedicalDocumentSchema:
        """Instantiate schema from a dictionary."""
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, json_str: str) -> MedicalDocumentSchema:
        """Instantiate schema from a JSON string."""
        return cls.model_validate_json(json_str)
