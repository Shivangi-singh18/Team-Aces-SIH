"""Integration tests for Module D FastAPI Router endpoints."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from module_d_abdm_privacy.router import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "storage_backend" in data


def test_abha_auth_flow():
    # 1. Request OTP
    req_payload = {"abha_id": "14-8921-3456-7890"}
    otp_res = client.post("/api/v1/auth/abha/request-otp", json=req_payload)
    assert otp_res.status_code == 200
    otp_data = otp_res.json()
    assert otp_data["success"] is True
    assert "txn_id" in otp_data
    txn_id = otp_data["txn_id"]

    # 2. Verify OTP
    verify_payload = {
        "abha_id": "14-8921-3456-7890",
        "otp": "123456",
        "txn_id": txn_id,
    }
    v_res = client.post("/api/v1/auth/abha/verify-otp", json=verify_payload)
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["success"] is True
    assert v_data["profile"]["name"] == "Ramesh Kumar"
    assert "access_token" in v_data
    assert "session_id" in v_data
    session_id = v_data["session_id"]

    # 3. Retrieve Session
    s_res = client.get(f"/api/v1/session/{session_id}")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["session_id"] == session_id

    # 4. Purge Session (DPDP Compliance)
    p_res = client.delete(f"/api/v1/session/purge?session_id={session_id}")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["success"] is True

    # 5. Verify Session Is Purged
    s_after = client.get(f"/api/v1/session/{session_id}")
    assert s_after.status_code == 404


def test_consent_creation_endpoint():
    consent_payload = {
        "abha_id": "14-8921-3456-7890",
        "scope": ["Prescription", "DiagnosticReport", "OPConsultation"],
        "hiu_id": "MEDIKIOSK_OPD_01",
        "purpose": "CARETREE",
        "doctor_name": "Dr. Anand",
        "cabin_number": "Cabin #4",
    }
    response = client.post("/api/v1/consent/create", json=consent_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "consent_id" in data
    artefact = data["consent_artefact"]
    assert artefact["requester"]["cabin"] == "Cabin #4"
    assert artefact["dpdp_compliance"]["notice_displayed_in_vernacular"] is True


def test_fhir_export_endpoint():
    export_payload = {
        "summary_payload": {
            "chief_complaints": ["Acute chest pain"],
            "patient_symptoms": ["Dyspnea"],
            "medical_history_summary": "Patient presented to kiosk with chest tightness.",
            "diagnoses": ["Angina Pectoris"],
            "icd10_codes": [{"code": "I20.9", "description": "Angina pectoris, unspecified"}],
            "medications": [
                {"drug_name": "Sorbitrate", "dosage": "5mg", "frequency": "SL SOS", "duration": "5 days"}
            ],
            "lab_results": [
                {"test_name": "Troponin-T", "value": "0.01", "unit": "ng/mL", "is_abnormal": False}
            ],
            "vitals": {
                "systolic_bp": 140,
                "diastolic_bp": 90,
                "heart_rate": 84,
                "spo2": 97,
            },
            "ayush_notes": {
                "prakriti": "Pitta",
                "vikriti": "Pitta-Vata aggravation",
            },
            "risk_assessment": {
                "risk_level": "High",
                "score": 8,
                "red_flags": ["Chest pain on exertion"],
                "recommended_specialty": "Cardiology",
            },
        },
        "abha_profile": {
            "abha_number": "14-8921-3456-7890",
            "abha_address": "ramesh.kumar@abdm",
            "name": "Ramesh Kumar",
            "gender": "M",
            "dob": "1965-04-12",
            "mobile": "+91-98765-43210",
        },
    }

    response = client.post("/api/v1/fhir/export", json=export_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["bundle_type"] == "document"
    assert data["total_resources"] >= 6
    bundle = data["bundle"]
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert bundle["entry"][0]["resource"]["resourceType"] == "Composition"
    assert bundle["entry"][1]["resource"]["resourceType"] == "Patient"

