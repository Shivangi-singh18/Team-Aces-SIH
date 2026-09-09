"""Pydantic v2 Data Contracts for Module D - ABDM & Privacy.

Defines schemas for:
- ABDM / ABHA OTP Generation and Profile Verification
- Consent Artefacts compliant with ABDM CM & DPDP Act 2023
- Clinical summary entities (Medication, LabResult, Vitals, AYUSH)
- FHIR R4 Bundle export requests and responses
- Ephemeral Session lifecycle models
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# =====================================================================
# 1. ABHA Authentication Schemas
# =====================================================================

class ABHAOTPRequest(BaseModel):
    """Payload for requesting an OTP for ABHA authentication."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    abha_id: str = Field(
        ...,
        description="14-digit ABHA Number (e.g. '14-8921-3456-7890' or '14892134567890') or ABHA Address (e.g. 'ramesh.kumar@abdm').",
        examples=["14-8921-3456-7890", "ramesh.kumar@abdm"],
    )

    @field_validator("abha_id")
    @classmethod
    def validate_abha_format(cls, v: str) -> str:
        clean = v.strip()
        # Accept ABHA address like username@abdm or username@sbx
        if "@" in clean:
            if not re.match(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$", clean):
                raise ValueError("Invalid ABHA Address format. Expected format: username@abdm")
            return clean

        # Accept numeric or hyphenated 14-digit ABHA number
        digits = re.sub(r"[-\s]", "", clean)
        if len(digits) != 14 or not digits.isdigit():
            raise ValueError("ABHA Number must be exactly 14 digits (e.g. 14-8921-3456-7890 or 14892134567890).")
        return clean


class ABHAOTPResponse(BaseModel):
    """Response payload when an OTP has been dispatched to the patient."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    success: bool = Field(default=True, description="Indicates whether OTP generation succeeded.")
    txn_id: str = Field(..., description="Unique ABDM transaction identifier for OTP verification.", examples=["txn-948b-3021-99af"])
    message: str = Field(..., description="User-facing status message in English.", examples=["OTP sent successfully to registered mobile number."])
    message_hi: Optional[str] = Field(
        default="पंजीकृत मोबाइल नंबर पर ओटीपी भेज दिया गया है।",
        description="Hindi localized status message for elderly patient kiosk interface.",
    )
    masked_mobile: str = Field(..., description="Masked recipient phone number for privacy.", examples=["******4321"])
    expires_in_seconds: int = Field(default=600, description="OTP validity window in seconds (10 minutes).")


class ABHAVerifyRequest(BaseModel):
    """Payload to verify an OTP and retrieve the authenticated ABHA profile."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    abha_id: str = Field(..., description="ABHA Number or ABHA Address provided during OTP request.")
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit One-Time Password received on registered mobile (Sandbox test default: '123456').",
        examples=["123456"],
    )
    txn_id: Optional[str] = Field(default=None, description="Transaction ID returned from request-otp.")


class ABHAAddress(BaseModel):
    """Structured residential address from ABHA registry."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    line: Optional[str] = Field(default="Ward 4, Civil Lines", description="Street / Locality.")
    district: Optional[str] = Field(default="Jaipur", description="District.")
    state: Optional[str] = Field(default="Rajasthan", description="State.")
    pincode: Optional[str] = Field(default="302001", description="Postal Pincode.")


class ABHAProfile(BaseModel):
    """Demographic profile retrieved from ABDM upon successful authentication."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    abha_number: str = Field(..., description="14-digit ABHA Number.", examples=["14-8921-3456-7890"])
    abha_address: str = Field(..., description="ABHA Address / PHR Handle.", examples=["ramesh.kumar@abdm"])
    name: str = Field(..., description="Full legal name of the patient.", examples=["Ramesh Kumar"])
    gender: Literal["M", "F", "O", "Male", "Female", "Other"] = Field(..., description="Gender.", examples=["M"])
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format.", examples=["1965-04-12"])
    mobile: str = Field(..., description="Patient mobile number.", examples=["+91-98765-43210"])
    address: Optional[ABHAAddress] = Field(default_factory=ABHAAddress, description="Structured postal address.")
    photo_url: Optional[str] = Field(default=None, description="URL or Base64 thumbnail photo.")
    kyc_verified: bool = Field(default=True, description="Indicates if Aadhaar / KYC verification is complete.")


class ABHAVerifyResponse(BaseModel):
    """Response payload returned upon successful ABHA verification."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    success: bool = Field(default=True, description="Verification success flag.")
    profile: ABHAProfile = Field(..., description="Patient ABHA demographic profile.")
    access_token: str = Field(..., description="ABDM X-Token / JWT bearer token for authorized session operations.")
    session_id: str = Field(..., description="Ephemeral MediKiosk session token created for this consultation.")
    message: str = Field(default="ABHA identity verified successfully.")


# =====================================================================
# 2. Consent Management & DPDP Act 2023 Schemas
# =====================================================================

class ConsentRequest(BaseModel):
    """Payload to request an ABDM consent artefact compliant with DPDP Act 2023."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    abha_id: str = Field(..., description="Patient ABHA identifier.", examples=["14-8921-3456-7890"])
    scope: List[str] = Field(
        default_factory=lambda: ["Prescription", "DiagnosticReport", "OPConsultation"],
        description="List of ABDM Health Information Types (HI Types) to grant access.",
        examples=[["Prescription", "DiagnosticReport", "OPConsultation"]],
    )
    hiu_id: Optional[str] = Field(
        default="MEDIKIOSK_OPD_01",
        description="Health Information User (HIU) ID of this OPD facility.",
        examples=["MEDIKIOSK_OPD_01"],
    )
    purpose: Optional[str] = Field(
        default="CARETREE",
        description="Standard ABDM Purpose Code (e.g. CARETREE for care management, PUBHLTH for public health).",
        examples=["CARETREE"],
    )
    doctor_name: Optional[str] = Field(
        default="Dr. Anand",
        description="Attending physician / clinician name for Cabin routing.",
        examples=["Dr. Anand"],
    )
    cabin_number: Optional[str] = Field(
        default="Cabin #4",
        description="Hospital OPD Cabin identifier.",
        examples=["Cabin #4"],
    )


class ConsentPermission(BaseModel):
    """Access control permission limits conforming to ABDM Consent Manager."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    access_mode: Literal["VIEW", "STORE", "STREAM", "QUERY"] = Field(
        default="VIEW",
        description="Mode of data access granted (MediKiosk defaults to strict ephemeral 'VIEW').",
    )
    date_range: Dict[str, str] = Field(
        default_factory=dict,
        description="Validity window of the clinical records being requested ('from' and 'to' ISO timestamps).",
    )
    data_erase_at: str = Field(
        ...,
        description="Exact ISO timestamp when data must be expunged from memory/cache.",
    )
    frequency: Dict[str, Any] = Field(
        default_factory=lambda: {"unit": "HOUR", "value": 1, "repeats": 0},
        description="Frequency policy for data exchange.",
    )


class DPDPComplianceMetadata(BaseModel):
    """Explicit governance metadata fulfilling India's DPDP Act 2023 requirements."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    regulation: str = Field(
        default="Digital Personal Data Protection Act, 2023 (DPDP Act 2023)",
        description="Governing statutory data privacy act.",
    )
    notice_displayed_in_vernacular: bool = Field(
        default=True,
        description="Affirms that bilingual (Hindi/English) consent notice with audio explanation was rendered.",
    )
    purpose_limitation: str = Field(
        default="Immediate triage and clinical consultation at MediKiosk Cabin #4 with Dr. Anand.",
        description="Strictly defined processing purpose (no secondary processing or advertising).",
    )
    ephemeral_processing: bool = Field(
        default=True,
        description="True indicates patient health records reside strictly in temporary RAM/TTL cache.",
    )
    retention_policy: str = Field(
        default="Immediate zero-knowledge wipe upon consultation completion or 15-minute auto-expiry.",
        description="Data retention boundary.",
    )
    patient_right_to_withdraw: bool = Field(
        default=True,
        description="Guarantees patient can toggle off consent at any moment before entering cabin.",
    )
    data_fiduciary: str = Field(
        default="MediKiosk Smart OPD & Ayushman Bharat Digital Mission (ABDM)",
        description="Entity acting as the Data Fiduciary under DPDP Act.",
    )


class ConsentArtefact(BaseModel):
    """Full ABDM Consent Artefact model with embedded DPDP Act governance."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    consent_id: str = Field(..., description="Globally unique UUID for the consent artefact.")
    status: Literal["REQUESTED", "GRANTED", "DENIED", "REVOKED", "EXPIRED"] = Field(
        default="GRANTED",
        description="Current state of consent.",
    )
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    patient_abha_id: str = Field(..., description="Subject ABHA identifier.")
    hiu: Dict[str, str] = Field(..., description="Health Information User metadata.")
    requester: Dict[str, Any] = Field(..., description="Doctor / Clinician requester metadata.")
    hi_types: List[str] = Field(..., description="Authorised Health Information Types.")
    permission: ConsentPermission = Field(..., description="Access permission constraints.")
    dpdp_compliance: DPDPComplianceMetadata = Field(
        default_factory=DPDPComplianceMetadata,
        description="DPDP Act 2023 statutory compliance declaration.",
    )


class ConsentResponse(BaseModel):
    """Response returned upon consent creation."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    success: bool = Field(default=True)
    consent_id: str = Field(..., description="Consent artefact UUID.")
    consent_artefact: ConsentArtefact = Field(..., description="Complete ABDM consent artefact.")
    message: str = Field(default="Consent artefact recorded and active under DPDP Act 2023 regulations.")


# =====================================================================
# 3. Clinical Data Contracts (Cross-Module B & LLM Engine)
# =====================================================================

class Medication(BaseModel):
    """Structured clinical medication entity."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    drug_name: str = Field(..., description="Name of medicine (generic/brand).", examples=["Amlodipine", "Metformin"])
    dosage: str = Field(..., description="Strength (e.g. 5mg, 500mg, 1 tab).", examples=["5mg"])
    frequency: str = Field(..., description="Frequency (e.g. 1-0-0, Once daily, TDS).", examples=["1-0-0"])
    duration: str = Field(..., description="Treatment duration (e.g. 30 days, 5 days).", examples=["30 days"])
    instructions: Optional[str] = Field(default=None, description="Special instructions.", examples=["Take after meals"])


class LabResult(BaseModel):
    """Structured diagnostic laboratory test result."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    test_name: str = Field(..., description="Name of lab test.", examples=["Fasting Blood Sugar", "Hemoglobin"])
    value: str = Field(..., description="Observed measurement value.", examples=["140", "13.5"])
    unit: str = Field(..., description="Measurement unit.", examples=["mg/dL", "g/dL"])
    is_abnormal: bool = Field(..., description="Flag indicating if test is outside normal reference range.", examples=[True])
    reference_range: Optional[str] = Field(default=None, description="Standard reference interval.", examples=["70-99 mg/dL"])


class VitalSigns(BaseModel):
    """Physiological vital signs recorded by kiosk sensors or nurse station."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    systolic_bp: Optional[int] = Field(default=None, description="Systolic Blood Pressure (mmHg).", examples=[138])
    diastolic_bp: Optional[int] = Field(default=None, description="Diastolic Blood Pressure (mmHg).", examples=[88])
    heart_rate: Optional[int] = Field(default=None, description="Pulse / Heart Rate (BPM).", examples=[76])
    spo2: Optional[int] = Field(default=None, description="Oxygen Saturation (%).", examples=[98])
    temperature_f: Optional[float] = Field(default=None, description="Body Temperature (deg F).", examples=[98.6])
    respiratory_rate: Optional[int] = Field(default=None, description="Breaths per minute.", examples=[16])


class AyushAssessment(BaseModel):
    """Traditional Indian Medicine (AYUSH) holistic assessment notes."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    prakriti: Optional[str] = Field(default="Vata-Pitta", description="Baseline constitutional dosha.", examples=["Vata-Pitta"])
    vikriti: Optional[str] = Field(default="Pitta imbalance", description="Current pathological imbalance.", examples=["Pitta imbalance"])
    dosha_imbalance: List[str] = Field(default_factory=lambda: ["Pitta", "Vata"], description="Active aggravated doshas.")
    lifestyle_recommendations: List[str] = Field(
        default_factory=lambda: ["Avoid excess spicy/fried foods", "Hydrate with room temperature water", "Practice Shitali Pranayama"],
        description="Holistic dietary and dinacharya recommendations.",
    )


class ClinicalSummaryPayload(BaseModel):
    """Consolidated clinical payload combining Module B OCR and Module LLM Engine."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    patient_id: Optional[str] = Field(default=None, description="Patient identifier or ABHA ID.")
    patient_demographics: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Demographics dictionary or serialized ABHAProfile.",
    )
    chief_complaints: List[str] = Field(
        default_factory=list,
        description="Primary reasons for visit.",
        examples=[["Chest discomfort", "Elevated blood sugar"]],
    )
    patient_symptoms: List[str] = Field(
        default_factory=list,
        description="Reported symptoms list.",
        examples=[["Exertional dyspnea", "Fatigue", "Polydipsia"]],
    )
    medical_history_summary: str = Field(
        default="",
        description="Clinical synthesis of patient history and present illness.",
        examples=["Elderly male patient presenting with chest tightness and history of diabetes."],
    )
    diagnoses: List[str] = Field(
        default_factory=list,
        description="Extracted or provisional diagnoses.",
        examples=[["Type 2 Diabetes Mellitus", "Essential Hypertension"]],
    )
    icd10_codes: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Standardized ICD-10 diagnostic codes.",
        examples=[[{"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"}]],
    )
    medications: List[Medication] = Field(
        default_factory=list,
        description="List of active medications.",
    )
    lab_results: List[LabResult] = Field(
        default_factory=list,
        description="List of extracted lab results.",
    )
    vitals: Optional[VitalSigns] = Field(
        default_factory=VitalSigns,
        description="Recorded physiological vital signs.",
    )
    ayush_notes: Optional[AyushAssessment] = Field(
        default_factory=AyushAssessment,
        description="AYUSH holistic evaluation.",
    )
    risk_assessment: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Risk triage categorization (level, score, red flags, specialty).",
    )
    voice_transcript: Optional[str] = Field(default=None, description="Voice intake transcript.")


# =====================================================================
# 4. FHIR R4 Export Schemas
# =====================================================================

class FHIRExportRequest(BaseModel):
    """Inbound request to convert clinical summary & OCR data into an HL7 FHIR R4 Bundle."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    summary_payload: ClinicalSummaryPayload = Field(
        ...,
        description="Synthesized clinical summary containing complaints, diagnoses, medications, labs, and vitals.",
    )
    abha_profile: Optional[ABHAProfile] = Field(
        default=None,
        description="Optional authenticated ABHA profile for mapping Patient resource.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for tracking ephemeral audit log.",
    )


class FHIRBundleResponse(BaseModel):
    """Export response containing the validated HL7 FHIR R4 Document Bundle."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    success: bool = Field(default=True)
    bundle_id: str = Field(..., description="UUID of the FHIR Bundle.")
    resource_type: str = Field(default="Bundle", description="HL7 FHIR Resource Type.")
    bundle_type: str = Field(default="document", description="Bundle type ('document' per HL7 R4).")
    total_resources: int = Field(..., description="Total count of entries inside the bundle.")
    composition_id: str = Field(..., description="ID of the root Composition resource.")
    patient_id: str = Field(..., description="ID of the associated Patient resource.")
    bundle: Dict[str, Any] = Field(..., description="Complete HL7 FHIR R4 Document Bundle JSON.")


# =====================================================================
# 5. Ephemeral Session Schemas
# =====================================================================

class SessionCreateRequest(BaseModel):
    """Payload to create an ephemeral patient session in Redis / TTL store."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    patient_id: str = Field(..., description="ABHA ID or temporary kiosk patient ID.", examples=["14-8921-3456-7890"])
    data: Dict[str, Any] = Field(default_factory=dict, description="Session state dictionary.")
    ttl_seconds: int = Field(
        default=900,
        ge=60,
        le=3600,
        description="Time-to-live in seconds (defaults to 900 seconds / 15 minutes).",
    )


class SessionResponse(BaseModel):
    """Response returned when querying an active ephemeral session."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    session_id: str = Field(...)
    patient_id: str = Field(...)
    created_at: str = Field(...)
    expires_at: str = Field(...)
    ttl_remaining_seconds: int = Field(...)
    storage_backend: Literal["redis", "in_memory"] = Field(...)
    data: Dict[str, Any] = Field(default_factory=dict)


class SessionPurgeRequest(BaseModel):
    """Payload to immediately wipe ephemeral kiosk patient data."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    session_id: str = Field(..., description="Unique session ID to wipe immediately.")


class SessionPurgeResponse(BaseModel):
    """Response returned after purging session data in compliance with DPDP Act."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    success: bool = Field(default=True)
    session_id: str = Field(...)
    message: str = Field(
        default="Patient session data immediately wiped with zero residue in strict accordance with DPDP Act 2023.",
    )
    purged_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

