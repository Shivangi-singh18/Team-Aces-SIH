"""Module D: ABDM / ABHA Integration, FHIR R4 Bundle Conversion, Consent Management, and Ephemeral Session Storage.

Project: MediKiosk Smart OPD (SIH26047)
Compliance: National Health Authority (NHA) ABDM Standards & DPDP Act 2023.
"""

from __future__ import annotations

from .abdm_client import (
    ABDMClient,
    abdm_client,
    client,
    generate_abha_otp,
    request_consent,
    verify_abha_otp,
)
from .fhir_converter import (
    FHIRConverter,
    convert_to_fhir_bundle,
    converter,
)
from .router import router
from .schemas import (
    ABHAAddress,
    ABHAOTPRequest,
    ABHAOTPResponse,
    ABHAProfile,
    ABHAVerifyRequest,
    ABHAVerifyResponse,
    AyushAssessment,
    ClinicalSummaryPayload,
    ConsentArtefact,
    ConsentPermission,
    ConsentRequest,
    ConsentResponse,
    DPDPComplianceMetadata,
    FHIRBundleResponse,
    FHIRExportRequest,
    LabResult,
    Medication,
    SessionCreateRequest,
    SessionPurgeRequest,
    SessionPurgeResponse,
    SessionResponse,
    VitalSigns,
)
from .session_manager import (
    SessionManager,
    create_session,
    get_session,
    purge_session,
    session_manager,
    update_session,
)

__version__ = "1.0.0"

__all__ = [
    # Router
    "router",
    # ABDM Client
    "ABDMClient",
    "client",
    "abdm_client",
    "generate_abha_otp",
    "verify_abha_otp",
    "request_consent",
    # FHIR Converter
    "FHIRConverter",
    "converter",
    "convert_to_fhir_bundle",
    # Ephemeral Session Manager
    "SessionManager",
    "session_manager",
    "create_session",
    "get_session",
    "update_session",
    "purge_session",
    # Schemas
    "ABHAOTPRequest",
    "ABHAOTPResponse",
    "ABHAVerifyRequest",
    "ABHAVerifyResponse",
    "ABHAProfile",
    "ABHAAddress",
    "ConsentRequest",
    "ConsentResponse",
    "ConsentArtefact",
    "ConsentPermission",
    "DPDPComplianceMetadata",
    "Medication",
    "LabResult",
    "VitalSigns",
    "AyushAssessment",
    "ClinicalSummaryPayload",
    "FHIRExportRequest",
    "FHIRBundleResponse",
    "SessionCreateRequest",
    "SessionResponse",
    "SessionPurgeRequest",
    "SessionPurgeResponse",
]

