"""MediKiosk LLM Orchestration Engine - Zero-API-Key Offline Mock Mode.

Provides deterministic, highly intelligent clinical triage logic and response
generation without requiring external network connectivity or paid API credentials.
Enables immediate testing and integration for mobile app and kiosk developers.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional
from .schemas import (
    ClinicalLLMResponse,
    ICD10Code,
    LLMProcessingRequest,
    RiskAssessment,
)


class ZeroApiKeyMockEngine:
    """Smart offline clinical inference engine.

    Parses clinical keywords, lab thresholds, medication contraindications,
    and triage indicators to produce realistic, schema-compliant responses.
    """

    # Keyword mappings for symptoms & specialties
    CLINICAL_KNOWLEDGE_BASE = [
        {
            "pattern": r"\b(chest pain|pain in (the |my )?chest|chest tightness|chest discomfort|angina|heart attack|palpitation|radiat(ing|es)? to (arm|jaw))\b",
            "complaint": "Acute chest pain and cardiovascular distress",
            "symptom": "Precordial chest discomfort / angina-like symptoms",
            "icd": ("R07.9", "Chest pain, unspecified"),
            "specialty": "Cardiology",
            "base_score": 8,
            "risk_level": "High",
            "red_flag": "Chest pain with potential cardiac involvement",
        },
        {
            "pattern": r"\b(shortness of breath|breathless|dyspnea|can't breathe|trouble breathing|wheezing|asthma)\b",
            "complaint": "Respiratory distress and shortness of breath",
            "symptom": "Acute dyspnea and respiratory effort",
            "icd": ("R06.02", "Shortness of breath"),
            "specialty": "Pulmonology",
            "base_score": 7,
            "risk_level": "High",
            "red_flag": "Acute respiratory compromise or dyspnea",
        },
        {
            "pattern": r"\b(high fever|fever|chills|shivering|temperature)\b",
            "complaint": "Acute febrile illness",
            "symptom": "Pyrexia / elevated body temperature",
            "icd": ("R50.9", "Fever, unspecified"),
            "specialty": "General Medicine",
            "base_score": 5,
            "risk_level": "Medium",
            "red_flag": None,
        },
        {
            "pattern": r"\b(cough|cold|sore throat|congestion|flu)\b",
            "complaint": "Upper respiratory tract infection symptoms",
            "symptom": "Persistent cough and pharyngeal irritation",
            "icd": ("J06.9", "Acute upper respiratory infection, unspecified"),
            "specialty": "General Medicine",
            "base_score": 3,
            "risk_level": "Low",
            "red_flag": None,
        },
        {
            "pattern": r"\b(stomach pain|abdominal pain|pain in (my |the )?stomach|vomiting|nausea|diarrhea|loose motions|gastric)\b",
            "complaint": "Acute gastrointestinal discomfort",
            "symptom": "Abdominal tenderness and gastrointestinal disturbance",
            "icd": ("R10.9", "Abdominal pain, unspecified"),
            "specialty": "Gastroenterology",
            "base_score": 4,
            "risk_level": "Medium",
            "red_flag": None,
        },
        {
            "pattern": r"\b(headache|pain in (my |the )?head|migraine|dizziness|fainting|vertigo|blackout)\b",
            "complaint": "Neurological distress and cephalalgia",
            "symptom": "Headache and postural instability / dizziness",
            "icd": ("R51.9", "Headache, unspecified"),
            "specialty": "Neurology",
            "base_score": 5,
            "risk_level": "Medium",
            "red_flag": None,
        },
        {
            "pattern": r"\b(diabetes|high sugar|glucose|hba1c|metformin|insulin)\b",
            "complaint": "Glycemic irregularity / Diabetic management",
            "symptom": "Hyperglycemia / diabetes mellitus monitoring",
            "icd": ("E11.9", "Type 2 diabetes mellitus without complications"),
            "specialty": "Endocrinology",
            "base_score": 4,
            "risk_level": "Medium",
            "red_flag": None,
        },
        {
            "pattern": r"\b(hypertension|high blood pressure|high bp|amlodipine|telmisartan)\b",
            "complaint": "Hypertension surveillance",
            "symptom": "Elevated arterial blood pressure",
            "icd": ("I10", "Essential (primary) hypertension"),
            "specialty": "Cardiology",
            "base_score": 4,
            "risk_level": "Medium",
            "red_flag": None,
        },
    ]

    def process(self, request: LLMProcessingRequest) -> ClinicalLLMResponse:
        """Process clinical input offline and return a structured ClinicalLLMResponse."""
        start_time = time.perf_counter()

        voice_text = (request.voice_transcript or "").strip().lower()
        ocr_data = request.ocr_data or {}
        demographics = request.patient_demographics or {}

        # Extracted containers
        chief_complaints: List[str] = []
        patient_symptoms: List[str] = []
        icd_codes: List[ICD10Code] = []
        red_flags: List[str] = []
        specialty_votes: Dict[str, int] = {}
        risk_score = 1
        history_points: List[str] = []

        # 1. Parse Voice Transcript
        if voice_text:
            for rule in self.CLINICAL_KNOWLEDGE_BASE:
                if re.search(rule["pattern"], voice_text, re.IGNORECASE):
                    chief_complaints.append(rule["complaint"])
                    patient_symptoms.append(rule["symptom"])
                    icd_codes.append(ICD10Code(code=rule["icd"][0], description=rule["icd"][1]))
                    if rule["red_flag"]:
                        red_flags.append(rule["red_flag"])
                    risk_score = max(risk_score, rule["base_score"])
                    spec = rule["specialty"]
                    specialty_votes[spec] = specialty_votes.get(spec, 0) + 2

        # 2. Parse OCR Data (Module B Contract)
        medications = ocr_data.get("medications", [])
        lab_results = ocr_data.get("lab_results", [])
        diagnoses = ocr_data.get("diagnoses", [])
        doc_type = ocr_data.get("document_type", "unknown")
        unparsed_text = ocr_data.get("unparsed_text", "")

        # Incorporate OCR diagnoses
        if diagnoses:
            for diag in diagnoses:
                chief_complaints.append(f"Recorded diagnosis: {diag}")
                history_points.append(f"Documented clinical history of {diag}")
                if any(k in diag.lower() for k in ["infarct", "stroke", "sepsis", "coronary", "failure"]):
                    risk_score = max(risk_score, 9)
                    red_flags.append(f"Critical diagnosis noted in prior records: {diag}")

        # Incorporate OCR medications
        med_summaries = []
        if medications:
            for med in medications:
                name = med.get("drug_name", "Unknown medication")
                dosage = med.get("dosage", "")
                freq = med.get("frequency", "")
                med_summaries.append(f"{name} ({dosage}, {freq})".strip())
            history_points.append(f"Current pharmacotherapy: {', '.join(med_summaries)}")

        # Incorporate OCR lab results & check abnormalities
        abnormal_labs = []
        if lab_results:
            for lab in lab_results:
                t_name = lab.get("test_name", "Lab test")
                val = lab.get("value", "")
                unit = lab.get("unit", "")
                is_abn = lab.get("is_abnormal", False)
                if is_abn:
                    abnormal_labs.append(f"{t_name}: {val} {unit}")
                    t_lower = t_name.lower()
                    if "glucose" in t_lower or "sugar" in t_lower:
                        try:
                            if float(val) > 250:
                                red_flags.append(f"Severe Hyperglycemia detected ({t_name}: {val} {unit})")
                                risk_score = max(risk_score, 8)
                        except ValueError:
                            pass
                    elif "creatinine" in t_lower:
                        try:
                            if float(val) > 2.0:
                                red_flags.append(f"Renal impairment indicated by elevated Creatinine ({val} {unit})")
                                risk_score = max(risk_score, 7)
                        except ValueError:
                            pass
                    elif "troponin" in t_lower or "d-dimer" in t_lower:
                        red_flags.append(f"Elevated cardiac/vascular biomarker ({t_name}: {val} {unit})")
                        risk_score = max(risk_score, 9)

            if abnormal_labs:
                history_points.append(f"Abnormal diagnostic findings: {'; '.join(abnormal_labs)}")
                risk_score = max(risk_score, 6)

        # 3. Demographics & Allergy Cross-Checking
        age = demographics.get("age")
        gender = demographics.get("gender")
        allergies = demographics.get("known_allergies") or demographics.get("allergies") or []
        if isinstance(allergies, str):
            allergies = [allergies]

        demo_desc = []
        if age:
            demo_desc.append(f"{age}-year-old")
            try:
                age_num = int(age)
                if age_num >= 65 and risk_score >= 5:
                    risk_score = min(10, risk_score + 1)
                    history_points.append(f"Geriatric vulnerability factor (Age {age_num})")
                elif age_num <= 5 and risk_score >= 5:
                    risk_score = min(10, risk_score + 1)
                    history_points.append(f"Pediatric vulnerability factor (Age {age_num})")
            except (ValueError, TypeError):
                pass
        if gender:
            demo_desc.append(f"{gender}")

        # Allergy contraindication detection
        if allergies:
            allergies_str = ", ".join(allergies)
            history_points.append(f"Documented drug allergies: {allergies_str}")
            for allergy in allergies:
                a_lower = allergy.lower()
                for med in medications:
                    m_lower = med.get("drug_name", "").lower()
                    if ("penicillin" in a_lower and any(p in m_lower for p in ["amox", "ampic", "penic", "augmentin"])) or \
                       ("sulfa" in a_lower and "bactrim" in m_lower) or \
                       (a_lower in m_lower):
                        red_flags.append(f"ALLERGY CONTRAINDICATION ALERT: Patient allergic to {allergy} but prescribed {med.get('drug_name')}")
                        risk_score = max(risk_score, 9)

        # 4. Fallback defaults if input was sparse
        if not chief_complaints:
            if voice_text:
                chief_complaints.append("General clinical consultation based on patient transcript")
                patient_symptoms.append(voice_text[:80])
            elif doc_type != "unknown":
                chief_complaints.append(f"Medical record review ({doc_type.replace('_', ' ').title()})")
            else:
                chief_complaints.append("Routine clinical health triage")

        if not patient_symptoms:
            patient_symptoms = ["Symptom evaluation pending physician review"]

        if not icd_codes:
            icd_codes.append(ICD10Code(code="Z00.00", description="Encounter for general adult medical examination"))

        # Deduplicate while preserving order
        chief_complaints = list(dict.fromkeys(chief_complaints))
        patient_symptoms = list(dict.fromkeys(patient_symptoms))
        seen_codes = set()
        dedup_icd = []
        for icd in icd_codes:
            if icd.code not in seen_codes:
                seen_codes.add(icd.code)
                dedup_icd.append(icd)
        icd_codes = dedup_icd
        red_flags = list(dict.fromkeys(red_flags))

        # 5. Determine Urgency Stratification
        if risk_score >= 9:
            risk_level = "Critical"
        elif risk_score >= 7:
            risk_level = "High"
        elif risk_score >= 4:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # 6. Determine Recommended Specialty
        if specialty_votes:
            recommended_specialty = max(specialty_votes, key=specialty_votes.get)
        else:
            if risk_score >= 8:
                recommended_specialty = "Emergency Medicine"
            else:
                recommended_specialty = "General Medicine"

        # 7. Synthesize Medical History Narrative
        subject = " ".join(demo_desc) if demo_desc else "Patient"
        narrative_parts = [f"{subject} presenting for clinical assessment."]
        if voice_text:
            narrative_parts.append(f"Reported symptoms include: '{voice_text[:120]}'.")
        if history_points:
            narrative_parts.append(" ".join(history_points) + ".")
        medical_history_summary = " ".join(narrative_parts)

        # 8. Patient-Friendly Instructions
        if risk_level in ("Critical", "High"):
            instructions = (
                f"Your symptoms have been flagged for priority attention by our medical team. "
                f"Please proceed immediately to the {recommended_specialty} triage station or alert the nearest nurse. "
                f"Avoid exerting yourself, sit down in the priority waiting area, and keep your phone accessible. "
                f"Staff have been notified of your arrival."
            )
        elif risk_level == "Medium":
            instructions = (
                f"Your medical summary has been prepared for the {recommended_specialty} physician. "
                f"Please take a seat in the waiting lounge. Keep hydrated, avoid strenuous activity, "
                f"and let the triage nurse know if your discomfort increases while waiting."
            )
        else:
            instructions = (
                f"Your intake evaluation is complete. Please proceed to the {recommended_specialty} reception "
                f"to receive your token number. A physician will consult with you shortly. "
                f"Remember to have your ID and prescription papers ready."
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ClinicalLLMResponse(
            chief_complaints=chief_complaints,
            patient_symptoms=patient_symptoms,
            medical_history_summary=medical_history_summary,
            icd10_codes=icd_codes,
            risk_assessment=RiskAssessment(
                risk_level=risk_level,
                score=risk_score,
                red_flags=red_flags,
                recommended_specialty=recommended_specialty,
            ),
            patient_friendly_instructions=instructions,
            provider_used="mock_offline",
            processing_time_ms=duration_ms,
        )


mock_engine = ZeroApiKeyMockEngine()
