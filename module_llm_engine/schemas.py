"""MediKiosk LLM Orchestration Engine - Pydantic v2 Data Contracts.

Defines strict request and response schemas matching the MediKiosk
mobile app and kiosk communication standards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ICD10Code(BaseModel):
    """ICD-10 clinical diagnosis or symptom code."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    code: str = Field(
        ...,
        description="Standard ICD-10 code (e.g., 'R07.9', 'E11.9', 'J06.9').",
        examples=["R07.9", "E11.9"],
    )
    description: str = Field(
        ...,
        description="Clinical description of the ICD-10 diagnosis or symptom.",
        examples=["Chest pain, unspecified", "Type 2 diabetes mellitus without complications"],
    )


class RiskAssessment(BaseModel):
    """Clinical triage risk assessment and urgency stratification."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        ...,
        description="Clinical triage category ('Low', 'Medium', 'High', 'Critical').",
        examples=["Medium"],
    )
    score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Urgency severity score on a scale from 1 (mild) to 10 (life-threatening emergency).",
        examples=[4],
    )
    red_flags: List[str] = Field(
        default_factory=list,
        description="Immediate clinical danger signs detected from symptoms, vitals, or lab anomalies.",
        examples=["Resting chest pain radiating to left arm", "Fasting glucose > 300 mg/dL"],
    )
    recommended_specialty: str = Field(
        ...,
        description="Recommended clinical department or medical specialty for referral.",
        examples=["General Medicine", "Cardiology", "Pulmonology"],
    )

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if not (1 <= v <= 10):
            raise ValueError("Risk score must be between 1 and 10 inclusive.")
        return v


class LLMProcessingRequest(BaseModel):
    """Inbound request payload sent by the mobile app or kiosk terminal."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    voice_transcript: Optional[str] = Field(
        default=None,
        description="Raw transcribed voice text or patient symptom narrative recorded via mobile microphone.",
        examples=["I have had a high fever for three days and chest tightness when breathing."],
    )
    ocr_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured OCR extraction dictionary matching Module B MedicalDocumentSchema.",
        examples=[
            {
                "document_type": "prescription",
                "diagnoses": ["Hypertension"],
                "medications": [
                    {"drug_name": "Amlodipine", "dosage": "5mg", "frequency": "1-0-0", "duration": "30 days"}
                ],
                "lab_results": [],
                "unparsed_text": "BP: 145/90 mmHg",
            }
        ],
    )
    patient_demographics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Patient background information including age, gender, and known allergies.",
        examples=[{"age": 45, "gender": "Male", "known_allergies": ["Penicillin"]}],
    )

    def has_content(self) -> bool:
        """Check if at least one meaningful clinical input is provided."""
        has_voice = bool(self.voice_transcript and self.voice_transcript.strip())
        has_ocr = bool(self.ocr_data and isinstance(self.ocr_data, dict) and any(self.ocr_data.values()))
        return has_voice or has_ocr


class ClinicalLLMResponse(BaseModel):
    """Structured clinical response returned to the mobile app or kiosk terminal."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    chief_complaints: List[str] = Field(
        default_factory=list,
        description="Primary clinical reasons for visit synthesized from voice and OCR records.",
        examples=[["Acute chest discomfort", "Persistent fever"]],
    )
    patient_symptoms: List[str] = Field(
        default_factory=list,
        description="Standardized list of clinical symptoms identified.",
        examples=[["Chest tightness", "Pyrexia", "Shortness of breath"]],
    )
    medical_history_summary: str = Field(
        ...,
        description="Comprehensive clinical narrative synthesizing past diagnoses, current medications, and lab trends.",
        examples=["Patient with known hypertension on Amlodipine presenting with acute chest discomfort."],
    )
    icd10_codes: List[ICD10Code] = Field(
        default_factory=list,
        description="ICD-10 clinical diagnostic and symptom codes.",
    )
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Triaged risk assessment detailing level, score, red flags, and specialty.",
    )
    patient_friendly_instructions: str = Field(
        ...,
        description="Simple, reassuring, jargon-free health instructions and navigation guidance for the patient UI.",
        examples=["Please sit down and rest. A doctor in General Medicine will see you shortly. Drink water and notify staff immediately if chest pain worsens."],
    )
    provider_used: Optional[str] = Field(
        default="mock_offline",
        description="Identifier of the backend engine that processed the request (e.g. 'gemini-1.5-flash', 'gpt-4o-mini', 'mock_offline').",
    )
    processing_time_ms: Optional[float] = Field(
        default=0.0,
        description="Processing latency in milliseconds.",
    )
