"""Unit tests for ABDM Mock & Sandbox Client."""

import pytest
from module_d_abdm_privacy.abdm_client import (
    ABDMClient,
    generate_abha_otp,
    request_consent,
    verify_abha_otp,
)


def test_generate_abha_otp_14_digit_success():
    res = generate_abha_otp("14-8921-3456-7890")
    assert res["success"] is True
    assert "txn_id" in res
    assert res["masked_mobile"].endswith("7890")
    assert res["expires_in_seconds"] == 600


def test_generate_abha_otp_address_format():
    res = generate_abha_otp("ramesh.kumar@abdm")
    assert res["success"] is True
    assert "txn_id" in res
    assert "******" in res["masked_mobile"]


def test_generate_abha_otp_invalid_format():
    with pytest.raises(ValueError, match="ABHA Number must be exactly 14 digits"):
        generate_abha_otp("12345")


def test_verify_abha_otp_success_default_sandbox():
    # First generate
    otp_resp = generate_abha_otp("14-8921-3456-7890")
    txn_id = otp_resp["txn_id"]

    # Verify using sandbox OTP
    auth_resp = verify_abha_otp("14-8921-3456-7890", "123456", txn_id=txn_id)
    assert auth_resp["success"] is True
    profile = auth_resp["profile"]
    assert profile["name"] == "Ramesh Kumar"
    assert profile["abha_number"] == "14-8921-3456-7890"
    assert profile["gender"] == "M"
    assert profile["dob"] == "1965-04-12"
    assert "access_token" in auth_resp
    assert "session_id" in auth_resp


def test_verify_abha_otp_invalid_otp():
    otp_resp = generate_abha_otp("14-8921-3456-7890")
    txn_id = otp_resp["txn_id"]

    with pytest.raises(ValueError, match="Invalid OTP"):
        verify_abha_otp("14-8921-3456-7890", "999999", txn_id=txn_id)


def test_request_consent_dpdp_compliance():
    scope = ["Prescription", "DiagnosticReport", "OPConsultation"]
    consent_res = request_consent(
        abha_id="14-8921-3456-7890",
        scope=scope,
        hiu_id="MEDIKIOSK_OPD_01",
        doctor_name="Dr. Anand",
        cabin_number="Cabin #4",
    )
    assert consent_res["success"] is True
    artefact = consent_res["consent_artefact"]

    assert artefact["status"] == "GRANTED"
    assert artefact["patient_abha_id"] == "14-8921-3456-7890"
    assert artefact["hiu"]["id"] == "MEDIKIOSK_OPD_01"
    assert artefact["requester"]["name"] == "Dr. Anand"
    assert artefact["requester"]["cabin"] == "Cabin #4"
    assert artefact["hi_types"] == scope
    assert artefact["permission"]["access_mode"] == "VIEW"

    dpdp = artefact["dpdp_compliance"]
    assert "DPDP Act 2023" in dpdp["regulation"]
    assert dpdp["notice_displayed_in_vernacular"] is True
    assert dpdp["ephemeral_processing"] is True
    assert dpdp["patient_right_to_withdraw"] is True

