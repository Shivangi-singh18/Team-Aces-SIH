"""Unit tests for FHIR R4 Bundle Converter."""

import pytest
from module_d_abdm_privacy.fhir_converter import convert_to_fhir_bundle
from module_d_abdm_privacy.schemas import (
    ABHAProfile,
    AyushAssessment,
    ClinicalSummaryPayload,
    LabResult,
    Medication,
    VitalSigns,
)


def test_fhir_converter_full_bundle():
    summary = ClinicalSummaryPayload(
        patient_id="14-8921-3456-7890",
        chief_complaints=["Chest tightness", "High fasting sugar"],
        patient_symptoms=["Exertional dyspnea", "Excessive thirst"],
        medical_history_summary="60-year-old male with long-standing Type-2 Diabetes and Hypertension.",
        diagnoses=["Type 2 Diabetes Mellitus", "Essential Hypertension"],
        icd10_codes=[
            {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
            {"code": "I10", "description": "Essential (primary) hypertension"},
        ],
        medications=[
            Medication(drug_name="Amlodipine", dosage="5mg", frequency="1-0-0", duration="30 days"),
            Medication(drug_name="Metformin", dosage="500mg", frequency="1-0-1", duration="30 days", instructions="After meals"),
        ],
        lab_results=[
            LabResult(test_name="Fasting Blood Sugar", value="158", unit="mg/dL", is_abnormal=True, reference_range="70-99 mg/dL"),
            LabResult(test_name="Hemoglobin", value="13.8", unit="g/dL", is_abnormal=False, reference_range="13.0-17.0 g/dL"),
        ],
        vitals=VitalSigns(
            systolic_bp=138,
            diastolic_bp=88,
            heart_rate=78,
            spo2=98,
            temperature_f=98.6,
        ),
        ayush_notes=AyushAssessment(
            prakriti="Vata-Pitta",
            vikriti="Pitta imbalance",
            dosha_imbalance=["Pitta"],
            lifestyle_recommendations=["Drink warm cumin water", "Avoid oily snacks"],
        ),
        risk_assessment={
            "risk_level": "Medium",
            "score": 5,
            "red_flags": [],
            "recommended_specialty": "General Medicine",
        },
    )

    profile = ABHAProfile(
        abha_number="14-8921-3456-7890",
        abha_address="ramesh.kumar@abdm",
        name="Ramesh Kumar",
        gender="M",
        dob="1965-04-12",
        mobile="+91-98765-43210",
    )

    bundle = convert_to_fhir_bundle(summary_payload=summary, abha_profile=profile)

    # 1. Bundle Top-Level Verification
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert "id" in bundle
    assert "entry" in bundle
    entries = bundle["entry"]
    assert len(entries) >= 7

    # 2. First entry MUST be Composition (HL7 Document Requirement)
    first_res = entries[0]["resource"]
    assert first_res["resourceType"] == "Composition"
    assert first_res["status"] == "final"
    assert first_res["type"]["coding"][0]["code"] == "34133-9"
    assert "subject" in first_res
    assert first_res["subject"]["display"] == "Ramesh Kumar"

    # Composition sections verification
    section_titles = [s["title"] for s in first_res["section"]]
    assert "Chief Complaints" in section_titles
    assert "History of Present Illness" in section_titles
    assert "Clinical Impressions & Diagnoses" in section_titles
    assert "Active & Prescribed Medications" in section_titles
    assert "Diagnostic Laboratory Results" in section_titles
    assert "Physiological Vital Signs" in section_titles
    assert "AYUSH Holistic & Prakriti Assessment" in section_titles
    assert "Clinical Triage & Risk Stratification" in section_titles

    # 3. Second entry MUST be Patient
    second_res = entries[1]["resource"]
    assert second_res["resourceType"] == "Patient"
    assert second_res["name"][0]["text"] == "Ramesh Kumar"
    assert second_res["gender"] == "male"
    assert second_res["birthDate"] == "1965-04-12"
    assert any(i["value"] == "14-8921-3456-7890" for i in second_res["identifier"])

    # 4. Conditions check
    cond_resources = [e["resource"] for e in entries if e["resource"]["resourceType"] == "Condition"]
    assert len(cond_resources) >= 2
    assert any(c.get("code", {}).get("coding", [{}])[0].get("code") == "E11.9" for c in cond_resources)

    # 5. MedicationStatement check
    med_resources = [e["resource"] for e in entries if e["resource"]["resourceType"] == "MedicationStatement"]
    assert len(med_resources) == 2
    med_names = [m["medicationCodeableConcept"]["text"] for m in med_resources]
    assert "Amlodipine" in med_names
    assert "Metformin" in med_names

    # 6. Observations check (Labs + Vitals)
    obs_resources = [e["resource"] for e in entries if e["resource"]["resourceType"] == "Observation"]
    assert len(obs_resources) >= 4  # 2 labs + vitals
    lab_obs = [o for o in obs_resources if o["category"][0]["coding"][0]["code"] == "laboratory"]
    assert len(lab_obs) == 2
    fbs_obs = next(o for o in lab_obs if o["code"]["text"] == "Fasting Blood Sugar")
    assert fbs_obs["valueQuantity"]["value"] == 158.0
    assert fbs_obs["interpretation"][0]["coding"][0]["code"] == "A"  # Abnormal


def test_fhir_converter_from_raw_dict():
    raw_summary = {
        "chief_complaints": ["Fever"],
        "diagnoses": ["Viral Fever"],
        "medications": [
            {"drug_name": "Paracetamol", "dosage": "650mg", "frequency": "TDS", "duration": "3 days"}
        ],
        "lab_results": [
            {"test_name": "Platelet Count", "value": "210000", "unit": "/uL", "is_abnormal": False}
        ],
    }

    bundle = convert_to_fhir_bundle(summary_payload=raw_summary)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert len(bundle["entry"]) >= 4

