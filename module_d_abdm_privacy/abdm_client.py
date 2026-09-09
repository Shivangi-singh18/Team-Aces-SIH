"""ABDM (Ayushman Bharat Digital Mission) Mock & Sandbox Client.

Provides simulation services for:
1. ABHA OTP generation & dispatch
2. ABHA identity verification & demographic profile resolution
3. ABDM Consent Artefact generation with explicit DPDP Act 2023 compliance
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("medikiosk.abdm")

# Sandbox default OTP for hackathon demo and testing
SANDBOX_DEMO_OTP = "123456"


class ABDMClient:
    """Mock sandbox client simulating National Health Authority (NHA) ABDM APIs."""

    def __init__(self) -> None:
        # In-memory store for active OTP transaction sessions
        self._txn_store: Dict[str, Dict[str, Any]] = {}

    def generate_abha_otp(self, abha_id: str) -> Dict[str, Any]:
        """Simulate generating and sending an OTP to the patient's registered mobile.

        Parameters
        ----------
        abha_id : str
            14-digit ABHA Number (e.g. '14-8921-3456-7890') or ABHA Address (e.g. 'ramesh.kumar@abdm').

        Returns
        -------
        Dict[str, Any]
            OTP dispatch response containing transaction ID, masked mobile, and status.
        """
        clean_id = abha_id.strip()
        logger.info("Initiating ABDM OTP generation for ABHA ID: %s", clean_id)

        # Basic format validation
        if "@" in clean_id:
            if not re.match(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$", clean_id):
                raise ValueError("Invalid ABHA Address format. Expected pattern: username@abdm")
            masked_mobile = "******4321"
        else:
            digits = re.sub(r"[-\s]", "", clean_id)
            if len(digits) != 14 or not digits.isdigit():
                raise ValueError("ABHA Number must be exactly 14 digits (e.g. 14-8921-3456-7890).")
            # Deterministic last 4 digits for realistic demo
            last_digits = digits[-4:]
            masked_mobile = f"******{last_digits}"

        txn_id = f"txn-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=10)

        # Save transaction context for verification
        self._txn_store[txn_id] = {
            "abha_id": clean_id,
            "expected_otp": SANDBOX_DEMO_OTP,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "masked_mobile": masked_mobile,
        }

        return {
            "success": True,
            "txn_id": txn_id,
            "message": "OTP sent successfully to registered mobile number.",
            "message_hi": "पंजीकृत मोबाइल नंबर पर 6-अंकों का ओटीपी भेजा गया है।",
            "masked_mobile": masked_mobile,
            "expires_in_seconds": 600,
        }

    def verify_abha_otp(
        self,
        abha_id: str,
        otp: str,
        txn_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify an OTP and return the authenticated ABHA profile and access token.

        Parameters
        ----------
        abha_id : str
            ABHA Number or ABHA Address provided during login.
        otp : str
            6-digit OTP received by patient. (Default sandbox OTP: '123456').
        txn_id : Optional[str]
            Transaction ID from generate_abha_otp.

        Returns
        -------
        Dict[str, Any]
            Profile payload with ABHA demographics, access token, and session ID.
        """
        clean_id = abha_id.strip()
        clean_otp = otp.strip()

        logger.info("Verifying ABDM OTP for ABHA ID: %s (txn: %s)", clean_id, txn_id)

        # Validate OTP
        if txn_id and txn_id in self._txn_store:
            txn = self._txn_store[txn_id]
            expected = txn.get("expected_otp", SANDBOX_DEMO_OTP)
            if clean_otp != expected and clean_otp != SANDBOX_DEMO_OTP:
                raise ValueError(f"Invalid OTP entered. Sandbox expected '{SANDBOX_DEMO_OTP}'.")
        else:
            # Allow verification using standard sandbox OTP even if txn_id omitted
            if clean_otp != SANDBOX_DEMO_OTP:
                raise ValueError(f"Invalid OTP entered. Sandbox expected '{SANDBOX_DEMO_OTP}'.")

        # Synthesize canonical profile matching MediKiosk senior citizen persona
        is_ramesh = "ramesh" in clean_id.lower() or "8921" in clean_id
        if is_ramesh or clean_id in ["14-8921-3456-7890", "ramesh.kumar@abdm"]:
            profile = {
                "abha_number": "14-8921-3456-7890",
                "abha_address": "ramesh.kumar@abdm",
                "name": "Ramesh Kumar",
                "gender": "M",
                "dob": "1965-04-12",
                "mobile": "+91-98765-43210",
                "address": {
                    "line": "Ward 4, Civil Lines",
                    "district": "Jaipur",
                    "state": "Rajasthan",
                    "pincode": "302001",
                },
                "photo_url": None,
                "kyc_verified": True,
            }
        else:
            # Fallback dynamic mock profile for arbitrary ABHA inputs
            digits = re.sub(r"[-\s]", "", clean_id)
            formatted_num = f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}-{digits[10:]}" if len(digits) == 14 else "14-5544-3322-1100"
            profile = {
                "abha_number": formatted_num,
                "abha_address": clean_id if "@" in clean_id else f"patient_{digits[-4:] if digits else 'test'}@abdm",
                "name": "Sunita Sharma" if "sunita" in clean_id.lower() else "Verified ABHA Patient",
                "gender": "F" if "sunita" in clean_id.lower() else "M",
                "dob": "1978-08-25",
                "mobile": "+91-98111-22334",
                "address": {
                    "line": "Flat 201, Green Park",
                    "district": "New Delhi",
                    "state": "Delhi",
                    "pincode": "110016",
                },
                "photo_url": None,
                "kyc_verified": True,
            }

        access_token = f"abdm_x_token_{uuid.uuid4().hex}"
        session_id = f"kiosk_sess_{uuid.uuid4().hex[:16]}"

        return {
            "success": True,
            "profile": profile,
            "access_token": access_token,
            "session_id": session_id,
            "message": "ABHA identity verified successfully.",
        }

    def request_consent(
        self,
        abha_id: str,
        scope: Optional[List[str]] = None,
        hiu_id: Optional[str] = "MEDIKIOSK_OPD_01",
        purpose: Optional[str] = "CARETREE",
        doctor_name: Optional[str] = "Dr. Anand",
        cabin_number: Optional[str] = "Cabin #4",
    ) -> Dict[str, Any]:
        """Generate an ABDM-compliant Consent Artefact with explicit DPDP Act 2023 compliance.

        Parameters
        ----------
        abha_id : str
            Patient ABHA identifier.
        scope : Optional[List[str]]
            Authorized Health Information Types (HI Types).
        hiu_id : Optional[str]
            Health Information User ID.
        purpose : Optional[str]
            ABDM Care purpose code ('CARETREE').
        doctor_name : Optional[str]
            Name of attending doctor for consultation cabin routing.
        cabin_number : Optional[str]
            Assigned OPD consultation room / cabin.

        Returns
        -------
        Dict[str, Any]
            Consent artefact conforming to ABDM Consent Manager specification.
        """
        clean_id = abha_id.strip()
        if not clean_id:
            raise ValueError("ABHA ID is required to generate consent artefact.")

        hi_types = scope if scope and len(scope) > 0 else ["Prescription", "DiagnosticReport", "OPConsultation"]
        now = datetime.now(timezone.utc)
        erase_time = now + timedelta(minutes=15)  # Strict 15-minute ephemeral lifespan
        consent_id = f"consent-{uuid.uuid4()}"

        artefact = {
            "consent_id": consent_id,
            "status": "GRANTED",
            "created_at": now.isoformat(),
            "patient_abha_id": clean_id,
            "hiu": {
                "id": hiu_id or "MEDIKIOSK_OPD_01",
                "name": "MediKiosk Smart OPD Terminal",
            },
            "requester": {
                "name": doctor_name or "Dr. Anand",
                "cabin": cabin_number or "Cabin #4",
                "identifier": {
                    "type": "REGNO",
                    "value": "MCI-48291",
                    "system": "https://nmc.org.in",
                },
            },
            "purpose": {
                "code": purpose or "CARETREE",
                "text": "Care Management and Real-Time Consultation",
                "refUri": "https://ndhm.gov.in/standards/purpose-codes",
            },
            "hi_types": hi_types,
            "permission": {
                "access_mode": "VIEW",
                "date_range": {
                    "from": (now - timedelta(days=365)).isoformat(),
                    "to": now.isoformat(),
                },
                "data_erase_at": erase_time.isoformat(),
                "frequency": {
                    "unit": "HOUR",
                    "value": 1,
                    "repeats": 0,
                },
            },
            "dpdp_compliance": {
                "regulation": "Digital Personal Data Protection Act, 2023 (DPDP Act 2023)",
                "notice_displayed_in_vernacular": True,
                "notice_languages": ["hi", "en"],
                "purpose_limitation": f"Immediate clinical consultation at {cabin_number or 'Cabin #4'} with {doctor_name or 'Dr. Anand'}.",
                "ephemeral_processing": True,
                "retention_policy": "Zero-knowledge immediate purge upon consultation handover or 15-minute auto-expiry.",
                "patient_right_to_withdraw": True,
                "data_fiduciary": "MediKiosk Smart OPD & Ayushman Bharat Digital Mission (ABDM)",
            },
        }

        logger.info("Created DPDP-compliant consent artefact %s for patient %s", consent_id, clean_id)
        return {
            "success": True,
            "consent_id": consent_id,
            "consent_artefact": artefact,
            "message": "Consent artefact recorded and active under DPDP Act 2023 regulations.",
        }


# Singleton client instance
client = ABDMClient()
abdm_client = client


# Convenience functional interface
def generate_abha_otp(abha_id: str) -> Dict[str, Any]:
    """Generate ABHA OTP using the singleton client."""
    return client.generate_abha_otp(abha_id)


def verify_abha_otp(abha_id: str, otp: str, txn_id: Optional[str] = None) -> Dict[str, Any]:
    """Verify ABHA OTP using the singleton client."""
    return client.verify_abha_otp(abha_id, otp, txn_id)


def request_consent(
    abha_id: str,
    scope: Optional[List[str]] = None,
    hiu_id: Optional[str] = None,
    purpose: Optional[str] = None,
    doctor_name: Optional[str] = None,
    cabin_number: Optional[str] = None,
) -> Dict[str, Any]:
    """Request and generate an ABDM & DPDP Act consent artefact using the singleton client."""
    return client.request_consent(
        abha_id=abha_id,
        scope=scope,
        hiu_id=hiu_id,
        purpose=purpose,
        doctor_name=doctor_name,
        cabin_number=cabin_number,
    )
