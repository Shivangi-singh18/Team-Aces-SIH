"""Clinical Summary Schemas for MediKiosk.

Defines Pydantic v2 data models for Medication, LabResult,
and ClinicalSummaryPayload for cross-module medical data exchange.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Medication(BaseModel):
    """Structured clinical medication entity."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    drug_name: str = Field(
        ...,
        description="Name of the medicine (brand name or generic name, e.g. Paracetamol, Amlodipine).",
        examples=["Amlodipine", "Metformin 500mg"],
    )
    dosage: str = Field(
        ...,
        description="Strength or dosage specification (e.g. 500mg, 10ml, 1 tablet).",
        examples=["5mg", "500mg"],
    )
    frequency: str = Field(
        ...,
        description="Frequency of administration (e.g. 1-0-1, OD, BD, TDS, Once daily, PRN).",
        examples=["1-0-0", "Once daily after meals"],
    )
    duration: str = Field(
        ...,
        description="Duration of the treatment (e.g. 5 days, 1 month, 30 days).",
        examples=["30 days", "5 days"],
    )
    instructions: Optional[str] = Field(
        default=None,
        description="Special instructions (e.g. take with warm water, avoid milk, after dinner).",
        examples=["Take before bedtime with warm water"],
    )


class LabResult(BaseModel):
    """Structured diagnostic laboratory test result."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    test_name: str = Field(
        ...,
        description="Name of the clinical test (e.g. Hemoglobin, Fasting Blood Sugar, HbA1c).",
        examples=["Fasting Blood Sugar", "Hemoglobin"],
    )
    value: str = Field(
        ...,
        description="Observed numeric or categorical result value (e.g. 13.5, 140, Positive).",
        examples=["140", "13.2"],
    )
    unit: str = Field(
        ...,
        description="Measurement unit (e.g. g/dL, mg/dL, mmol/L, %).",
        examples=["mg/dL", "g/dL"],
    )
    is_abnormal: bool = Field(
        ...,
        description="Flag indicating if the test value lies outside the normal reference range.",
        examples=[True, False],
    )
    reference_range: Optional[str] = Field(
        default=None,
        description="Normal reference range for this lab test (e.g. 70-100 mg/dL).",
        examples=["70-99 mg/dL", "13.0-17.0 g/dL"],
    )


class ClinicalSummaryPayload(BaseModel):
    """Comprehensive clinical intake and summary payload.

    Synthesizes patient voice intake, digitized OCR reports,
    prescriptions, vital signs, and AYUSH holistic assessments.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    patient_id: Optional[str] = Field(
        default=None,
        description="Patient unique identifier or ABHA ID (e.g. 14-8921-3456-7890).",
        examples=["14-8921-3456-7890"],
    )
    patient_demographics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Patient demographic metadata (name, age, gender, known allergies).",
        examples=[{"name": "Ramesh Kumar", "age": 60, "gender": "Male", "allergies": ["Penicillin"]}],
    )
    chief_complaints: List[str] = Field(
        default_factory=list,
        description="Primary reasons for hospital/kiosk visit.",
        examples=[["Acute chest tightness", "Elevated blood sugar"]],
    )
    patient_symptoms: List[str] = Field(
        default_factory=list,
        description="Standardized list of symptoms reported by the patient.",
        examples=[["Exertional dyspnea", "Excessive thirst", "Fatigue"]],
    )
    medical_history_summary: str = Field(
        default="",
        description="Synthesized clinical narrative summarizing past history, present illness, and findings.",
        examples=["Elderly patient with long-standing Type-2 Diabetes and Hypertension presenting with exertion fatigue."],
    )
    diagnoses: List[str] = Field(
        default_factory=list,
        description="Preliminary, differential, or historical diagnoses.",
        examples=[["Type 2 Diabetes Mellitus", "Essential Hypertension"]],
    )
    icd10_codes: List[Dict[str, str]] = Field(
        default_factory=list,
        description="ICD-10 clinical coding entries with code and description.",
        examples=[[{"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"}]],
    )
    medications: List[Medication] = Field(
        default_factory=list,
        description="List of active or newly prescribed medications.",
    )
    lab_results: List[LabResult] = Field(
        default_factory=list,
        description="List of lab pathology parameters and diagnostic observations.",
    )
    vitals: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Patient vital signs (e.g. Blood Pressure, Heart Rate, SpO2, Temperature).",
        examples=[{"systolic_bp": 138, "diastolic_bp": 88, "heart_rate": 78, "spo2": 98, "temperature_f": 98.6}],
    )
    ayush_notes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Holistic AYUSH assessment notes (Prakriti, Vikriti, Agni state, dietary guidance).",
        examples=[{"prakriti": "Vata-Pitta", "vikriti": "Pitta imbalance", "lifestyle_tips": ["Avoid spicy foods", "Hydrate with warm cumin water"]}],
    )
    risk_assessment: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Clinical risk triage assessment (risk level, severity score 1-10, red flags, specialty referral).",
        examples=[{"risk_level": "Medium", "score": 5, "red_flags": [], "recommended_specialty": "General Medicine"}],
    )
    voice_transcript: Optional[str] = Field(
        default=None,
        description="Raw transcribed voice intake text recorded at kiosk or mobile.",
    )
    unparsed_text: Optional[str] = Field(
        default=None,
        description="Any residual doctor notes or unclassified text.",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to a standard dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Serialize payload to a formatted JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClinicalSummaryPayload:
        """Instantiate schema from a dictionary."""
        return cls.model_validate(data)

