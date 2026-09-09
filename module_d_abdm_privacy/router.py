"""FastAPI APIRouter for Module D (ABDM Integration, FHIR R4, Consent, & Session Privacy).

Endpoints:
- POST   /api/v1/auth/abha/request-otp : Initiates ABHA OTP dispatch
- POST   /api/v1/auth/abha/verify-otp  : Authenticates patient & resolves ABHA profile
- POST   /api/v1/consent/create        : Generates DPDP-compliant ABDM consent artefact
- POST   /api/v1/fhir/export           : Synthesizes LLM + OCR summaries into FHIR R4 Bundle
- DELETE /api/v1/session/purge         : Immediately wipes patient data per DPDP Act 2023
- GET    /api/v1/session/{session_id}  : Inspects active ephemeral kiosk session
- GET    /api/v1/health                : Health check probe
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status

from .abdm_client import abdm_client, generate_abha_otp, request_consent, verify_abha_otp
from .fhir_converter import convert_to_fhir_bundle
from .schemas import (
    ABHAOTPRequest,
    ABHAOTPResponse,
    ABHAProfile,
    ABHAVerifyRequest,
    ABHAVerifyResponse,
    ConsentRequest,
    ConsentResponse,
    FHIRBundleResponse,
    FHIRExportRequest,
    SessionPurgeRequest,
    SessionPurgeResponse,
    SessionResponse,
)
from .session_manager import create_session, get_session, purge_session, session_manager

logger = logging.getLogger("medikiosk.router")

router = APIRouter(prefix="/api/v1", tags=["Module D: ABDM & Privacy"])


@router.get("/health", summary="Health Check for Module D Backend")
async def health_check() -> Dict[str, Any]:
    """Inspect availability of ABDM Sandbox and Session storage backends."""
    return {
        "status": "healthy",
        "module": "Module D: ABDM Integration, FHIR R4, & DPDP Privacy",
        "version": "1.0.0",
        "storage_backend": "redis" if session_manager.is_using_redis else "in_memory",
        "dpdp_ephemeral_enforced": True,
        "default_session_ttl_seconds": session_manager.default_ttl,
    }


# =====================================================================
# 1. ABHA Authentication Endpoints
# =====================================================================

@router.post(
    "/auth/abha/request-otp",
    response_model=ABHAOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP for ABHA authentication",
)
async def api_request_abha_otp(payload: ABHAOTPRequest) -> ABHAOTPResponse:
    """Simulate ABDM OTP dispatch to patient mobile."""
    try:
        result = generate_abha_otp(payload.abha_id)
        return ABHAOTPResponse.model_validate(result)
    except ValueError as val_err:
        logger.warning("ABHA OTP request validation error: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.error("Failed to generate ABHA OTP: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal ABDM Gateway error: {str(exc)}",
        ) from exc


@router.post(
    "/auth/abha/verify-otp",
    response_model=ABHAVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify ABHA OTP and obtain profile",
)
async def api_verify_abha_otp(payload: ABHAVerifyRequest) -> ABHAVerifyResponse:
    """Verify ABHA OTP and automatically provision an ephemeral kiosk session."""
    try:
        auth_data = verify_abha_otp(
            abha_id=payload.abha_id,
            otp=payload.otp,
            txn_id=payload.txn_id,
        )

        profile_dict = auth_data["profile"]
        session_id = auth_data["session_id"]

        # Automatically create ephemeral session in Redis / In-Memory
        session_manager.create_session(
            patient_id=profile_dict.get("abha_number", payload.abha_id),
            data={
                "profile": profile_dict,
                "access_token": auth_data["access_token"],
                "authenticated_at": auth_data.get("created_at"),
            },
        )

        return ABHAVerifyResponse(
            success=True,
            profile=ABHAProfile.model_validate(profile_dict),
            access_token=auth_data["access_token"],
            session_id=session_id,
            message=auth_data.get("message", "ABHA identity verified successfully."),
        )
    except ValueError as val_err:
        logger.warning("ABHA OTP verification failed: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.error("Failed to verify ABHA OTP: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal authentication error: {str(exc)}",
        ) from exc


# =====================================================================
# 2. Consent Management & DPDP Act 2023 Endpoints
# =====================================================================

@router.post(
    "/consent/create",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create DPDP-compliant ABDM Consent Artefact",
)
async def api_create_consent(payload: ConsentRequest) -> ConsentResponse:
    """Generate an ABDM consent artefact with explicit DPDP Act 2023 statutory compliance."""
    try:
        result = request_consent(
            abha_id=payload.abha_id,
            scope=payload.scope,
            hiu_id=payload.hiu_id,
            purpose=payload.purpose,
            doctor_name=payload.doctor_name,
            cabin_number=payload.cabin_number,
        )
        return ConsentResponse.model_validate(result)
    except ValueError as val_err:
        logger.warning("Consent creation validation error: %s", val_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except Exception as exc:
        logger.error("Failed to create consent artefact: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consent creation failed: {str(exc)}",
        ) from exc


# =====================================================================
# 3. FHIR R4 Bundle Conversion Endpoint
# =====================================================================

@router.post(
    "/fhir/export",
    response_model=FHIRBundleResponse,
    status_code=status.HTTP_200_OK,
    summary="Export combined clinical summary & OCR data as HL7 FHIR R4 Bundle",
)
async def api_export_fhir(payload: FHIRExportRequest) -> FHIRBundleResponse:
    """Convert combined LLM clinical summary, prescriptions, lab results, and vitals into FHIR R4."""
    try:
        bundle = convert_to_fhir_bundle(
            summary_payload=payload.summary_payload,
            abha_profile=payload.abha_profile,
        )

        bundle_id = bundle.get("id", "")
        entries = bundle.get("entry", [])
        total_resources = len(entries)

        composition_id = ""
        patient_id = ""

        if entries and len(entries) > 0:
            first_res = entries[0].get("resource", {})
            if first_res.get("resourceType") == "Composition":
                composition_id = first_res.get("id", "")

        if len(entries) > 1:
            second_res = entries[1].get("resource", {})
            if second_res.get("resourceType") == "Patient":
                patient_id = second_res.get("id", "")

        # Optionally persist export into session cache if session_id passed
        if payload.session_id:
            session_manager.update_session(payload.session_id, {"fhir_bundle": bundle})

        return FHIRBundleResponse(
            success=True,
            bundle_id=bundle_id,
            resource_type="Bundle",
            bundle_type="document",
            total_resources=total_resources,
            composition_id=composition_id,
            patient_id=patient_id,
            bundle=bundle,
        )
    except Exception as exc:
        logger.error("Error generating FHIR R4 Bundle: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR R4 Bundle conversion failed: {str(exc)}",
        ) from exc


# =====================================================================
# 4. Ephemeral Session & DPDP Purge Endpoints
# =====================================================================

@router.delete(
    "/session/purge",
    response_model=SessionPurgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Immediately wipe patient data from kiosk (DPDP Act 2023 Compliance)",
)
async def api_purge_session(
    session_id: Optional[str] = Query(None, description="Session ID passed as query parameter"),
    body: Optional[SessionPurgeRequest] = None,
) -> SessionPurgeResponse:
    """Immediately wipes ephemeral patient records from memory/cache post-consultation."""
    target_id = session_id or (body.session_id if body else None)
    if not target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide session_id via query parameter (?session_id=...) or JSON body.",
        )

    purged = purge_session(target_id)
    return SessionPurgeResponse(
        success=True,
        session_id=target_id,
        message=(
            "Patient data successfully wiped with zero residue in strict compliance with DPDP Act 2023."
            if purged
            else "Session was already expired or purged."
        ),
    )


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect active kiosk session state",
)
async def api_get_session(session_id: str) -> SessionResponse:
    """Inspect active session state and remaining TTL window."""
    record = get_session(session_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' has expired or does not exist (DPDP Act minimal retention).",
        )

    return SessionResponse.model_validate(record)

