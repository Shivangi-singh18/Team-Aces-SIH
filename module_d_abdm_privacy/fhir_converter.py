"""FHIR R4 Bundle Converter (Module D - MediKiosk).

Transforms multi-modal patient summaries (voice intake, digitized OCR,
clinical triage, and AYUSH assessments) into strictly compliant HL7 FHIR R4
document bundles conforming to ABDM (Ayushman Bharat Digital Mission) standards.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .schemas import (
    ABHAProfile,
    AyushAssessment,
    ClinicalSummaryPayload,
    LabResult,
    Medication,
    VitalSigns,
)

logger = logging.getLogger("medikiosk.fhir")

# Standard LOINC & SNOMED CT terminology identifiers
LOINC_DOC_SUMMARY = "34133-9"  # Summary of episode note
LOINC_CHIEF_COMPLAINT = "10154-3"  # Chief complaint
LOINC_HPI = "10164-2"  # History of present illness
LOINC_PAST_HX = "11348-0"  # History of past illness
LOINC_MEDICATIONS = "10160-0"  # History of medication use
LOINC_LAB_RESULTS = "30954-2"  # Relevant diagnostic tests/laboratory data
LOINC_VITAL_SIGNS = "8716-3"  # Vital signs
LOINC_TRIAGE = "54094-8"  # Emergency department triage note

# Specific vital sign LOINCs
LOINC_HEART_RATE = "8867-4"
LOINC_O2_SAT = "59408-5"
LOINC_BODY_TEMP = "8310-5"
LOINC_RESP_RATE = "9279-1"
LOINC_BP_PANEL = "85354-9"
LOINC_BP_SYSTOLIC = "8480-6"
LOINC_BP_DIASTOLIC = "8462-4"


class FHIRConverter:
    """Orchestrates conversion of clinical inputs to HL7 FHIR R4 Document Bundle."""

    def __init__(self, organization_name: str = "MediKiosk Smart OPD", facility_id: str = "MEDIKIOSK_OPD_01") -> None:
        self.organization_name = organization_name
        self.facility_id = facility_id

    def convert_to_fhir_bundle(
        self,
        summary_payload: Union[ClinicalSummaryPayload, Dict[str, Any]],
        abha_profile: Optional[Union[ABHAProfile, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Convert clinical summary and demographic data into a valid FHIR R4 Document Bundle.

        Per HL7 FHIR R4 specifications for Document Bundles:
        1. Bundle.type MUST be 'document'.
        2. First entry in Bundle.entry MUST be a Composition resource.
        3. Composition.subject MUST reference the Patient resource.
        4. Composition.section entries link to Condition, MedicationStatement, and Observation resources.

        Parameters
        ----------
        summary_payload : Union[ClinicalSummaryPayload, Dict[str, Any]]
            Synthesized clinical summary from Module LLM Engine & Module B OCR.
        abha_profile : Optional[Union[ABHAProfile, Dict[str, Any]]]
            Authenticated ABHA demographic profile.

        Returns
        -------
        Dict[str, Any]
            HL7 FHIR R4 Bundle JSON dictionary.
        """
        # Normalize input to ClinicalSummaryPayload
        if isinstance(summary_payload, dict):
            summary = self._dict_to_summary_payload(summary_payload)
        else:
            summary = summary_payload

        # Normalize ABHA profile
        profile = self._normalize_profile(abha_profile, summary.patient_demographics)

        now_iso = datetime.now(timezone.utc).isoformat()
        bundle_id = str(uuid.uuid4())
        composition_id = str(uuid.uuid4())
        patient_id = str(uuid.uuid4())

        patient_ref = f"urn:uuid:{patient_id}"
        patient_display = profile.get("name", "Ramesh Kumar")

        entries: List[Dict[str, Any]] = []
        section_references: Dict[str, List[Dict[str, str]]] = {
            "conditions": [],
            "medications": [],
            "labs": [],
            "vitals": [],
        }

        # -------------------------------------------------------------
        # 1. Build Patient Resource
        # -------------------------------------------------------------
        patient_resource = self._build_patient_resource(patient_id, profile)
        patient_entry = {
            "fullUrl": patient_ref,
            "resource": patient_resource,
        }

        # -------------------------------------------------------------
        # 2. Build Condition Resources (Diagnoses & ICD-10 Codes)
        # -------------------------------------------------------------
        conditions = self._build_condition_resources(summary, patient_ref, patient_display, now_iso)
        for cond in conditions:
            cond_ref = f"urn:uuid:{cond['id']}"
            entries.append({"fullUrl": cond_ref, "resource": cond})
            section_references["conditions"].append({"reference": cond_ref, "display": cond.get("code", {}).get("text", "Diagnosis")})

        # -------------------------------------------------------------
        # 3. Build MedicationStatement Resources
        # -------------------------------------------------------------
        med_resources = self._build_medication_resources(summary.medications, patient_ref, patient_display, now_iso)
        for med in med_resources:
            med_ref = f"urn:uuid:{med['id']}"
            entries.append({"fullUrl": med_ref, "resource": med})
            section_references["medications"].append({"reference": med_ref, "display": med.get("medicationCodeableConcept", {}).get("text", "Medication")})

        # -------------------------------------------------------------
        # 4. Build Observation Resources (Labs & Vitals)
        # -------------------------------------------------------------
        lab_observations = self._build_lab_observations(summary.lab_results, patient_ref, patient_display, now_iso)
        for lab in lab_observations:
            lab_ref = f"urn:uuid:{lab['id']}"
            entries.append({"fullUrl": lab_ref, "resource": lab})
            section_references["labs"].append({"reference": lab_ref, "display": lab.get("code", {}).get("text", "Laboratory Result")})

        vital_observations = self._build_vital_observations(summary.vitals, patient_ref, patient_display, now_iso)
        for vital in vital_observations:
            vital_ref = f"urn:uuid:{vital['id']}"
            entries.append({"fullUrl": vital_ref, "resource": vital})
            section_references["vitals"].append({"reference": vital_ref, "display": vital.get("code", {}).get("text", "Vital Sign")})

        # -------------------------------------------------------------
        # 5. Build Composition Resource (ROOT Entry)
        # -------------------------------------------------------------
        composition_resource = self._build_composition_resource(
            composition_id=composition_id,
            patient_ref=patient_ref,
            patient_display=patient_display,
            summary=summary,
            section_references=section_references,
            created_at=now_iso,
        )
        composition_entry = {
            "fullUrl": f"urn:uuid:{composition_id}",
            "resource": composition_resource,
        }

        # -------------------------------------------------------------
        # Assemble Bundle (Composition MUST be entry[0])
        # -------------------------------------------------------------
        all_entries = [composition_entry, patient_entry] + entries

        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "identifier": {
                "system": "https://medikiosk.gov.in/bundles",
                "value": f"bundle-{bundle_id}",
            },
            "type": "document",
            "timestamp": now_iso,
            "entry": all_entries,
        }

        logger.info(
            "Synthesized HL7 FHIR R4 Bundle %s for patient %s (%d total entries)",
            bundle_id,
            patient_display,
            len(all_entries),
        )

        return bundle

    # -----------------------------------------------------------------
    # Helper Builder Methods
    # -----------------------------------------------------------------

    def _build_patient_resource(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Build standard FHIR R4 Patient resource."""
        raw_gender = str(profile.get("gender", "male")).lower()
        if raw_gender in ["m", "male"]:
            fhir_gender = "male"
        elif raw_gender in ["f", "female"]:
            fhir_gender = "female"
        else:
            fhir_gender = "other"

        name = profile.get("name", "Ramesh Kumar")
        name_parts = name.split(" ")
        family = name_parts[-1] if len(name_parts) > 1 else ""
        given = name_parts[:-1] if len(name_parts) > 1 else [name]

        identifiers = []
        if profile.get("abha_number"):
            identifiers.append({
                "system": "https://healthid.ndhm.gov.in",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR", "display": "Medical record number"}]},
                "value": profile["abha_number"],
            })
        if profile.get("abha_address"):
            identifiers.append({
                "system": "https://ndhm.gov.in/phr",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "SB", "display": "Social Beneficiary Identifier"}]},
                "value": profile["abha_address"],
            })

        address_dict = profile.get("address") or {}
        address_line = address_dict.get("line", "Ward 4, Civil Lines")
        city = address_dict.get("district", "Jaipur")
        state = address_dict.get("state", "Rajasthan")
        pincode = address_dict.get("pincode", "302001")

        telecom = []
        if profile.get("mobile"):
            telecom.append({
                "system": "phone",
                "value": profile["mobile"],
                "use": "mobile",
            })

        return {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": identifiers,
            "active": True,
            "name": [{
                "use": "official",
                "text": name,
                "family": family,
                "given": given,
            }],
            "telecom": telecom,
            "gender": fhir_gender,
            "birthDate": profile.get("dob", "1965-04-12"),
            "address": [{
                "use": "home",
                "type": "both",
                "line": [address_line],
                "city": city,
                "state": state,
                "postalCode": pincode,
                "country": "IND",
            }],
        }

    def _build_composition_resource(
        self,
        composition_id: str,
        patient_ref: str,
        patient_display: str,
        summary: ClinicalSummaryPayload,
        section_references: Dict[str, List[Dict[str, str]]],
        created_at: str,
    ) -> Dict[str, Any]:
        """Build the root Composition resource linking all sections and narratives."""
        sections: List[Dict[str, Any]] = []

        # 1. Chief Complaints Section
        if summary.chief_complaints:
            complaint_html = "<ul>" + "".join(f"<li>{c}</li>" for c in summary.chief_complaints) + "</ul>"
            sections.append({
                "title": "Chief Complaints",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_CHIEF_COMPLAINT, "display": "Chief complaint"}],
                    "text": "Chief Complaints",
                },
                "text": {
                    "status": "generated",
                    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{complaint_html}</div>",
                },
            })

        # 2. History of Present Illness (HPI) & Reported Symptoms
        hpi_narrative = summary.medical_history_summary or "Patient attended MediKiosk OPD intake terminal."
        symptoms_str = ", ".join(summary.patient_symptoms) if summary.patient_symptoms else "None reported"
        sections.append({
            "title": "History of Present Illness",
            "code": {
                "coding": [{"system": "http://loinc.org", "code": LOINC_HPI, "display": "History of Present illness Narrative"}],
                "text": "History of Present Illness",
            },
            "text": {
                "status": "generated",
                "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>{hpi_narrative}</p><p><strong>Reported Symptoms:</strong> {symptoms_str}</p></div>",
            },
        })

        # 3. Diagnoses / Conditions Section
        if section_references["conditions"]:
            diag_html = "<ul>" + "".join(f"<li>{item['display']}</li>" for item in section_references["conditions"]) + "</ul>"
            sections.append({
                "title": "Clinical Impressions & Diagnoses",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_PAST_HX, "display": "History of Past illness"}],
                    "text": "Diagnoses",
                },
                "text": {
                    "status": "generated",
                    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{diag_html}</div>",
                },
                "entry": section_references["conditions"],
            })

        # 4. Medications Section
        if section_references["medications"]:
            med_html = "<ul>" + "".join(f"<li>{item['display']}</li>" for item in section_references["medications"]) + "</ul>"
            sections.append({
                "title": "Active & Prescribed Medications",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_MEDICATIONS, "display": "History of Medication use"}],
                    "text": "Medications",
                },
                "text": {
                    "status": "generated",
                    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{med_html}</div>",
                },
                "entry": section_references["medications"],
            })

        # 5. Lab Results Section
        if section_references["labs"]:
            lab_html = "<ul>" + "".join(f"<li>{item['display']}</li>" for item in section_references["labs"]) + "</ul>"
            sections.append({
                "title": "Diagnostic Laboratory Results",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_LAB_RESULTS, "display": "Relevant diagnostic tests/laboratory data"}],
                    "text": "Laboratory Findings",
                },
                "text": {
                    "status": "generated",
                    "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{lab_html}</div>",
                },
                "entry": section_references["labs"],
            })

        # 6. Vital Signs Section
        if section_references["vitals"]:
            sections.append({
                "title": "Physiological Vital Signs",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_VITAL_SIGNS, "display": "Vital signs"}],
                    "text": "Vital Signs",
                },
                "text": {
                    "status": "generated",
                    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Vital signs captured at MediKiosk biometric terminal.</p></div>",
                },
                "entry": section_references["vitals"],
            })

        # 7. AYUSH Holistic Assessment Section (Traditional Medicine integration)
        ayush = summary.ayush_notes
        prakriti = getattr(ayush, "prakriti", None) if ayush else None
        vikriti = getattr(ayush, "vikriti", None) if ayush else None
        doshas = getattr(ayush, "dosha_imbalance", []) if ayush else []
        lifestyle = getattr(ayush, "lifestyle_recommendations", []) if ayush else []

        if prakriti or vikriti:
            ayush_html = (
                f"<div xmlns=\"http://www.w3.org/1999/xhtml\">"
                f"<p><strong>Baseline Prakriti:</strong> {prakriti or 'Not specified'}</p>"
                f"<p><strong>Vikriti Imbalance:</strong> {vikriti or 'Balanced'}</p>"
                f"<p><strong>Aggravated Doshas:</strong> {', '.join(doshas) if doshas else 'None'}</p>"
                f"<p><strong>Holistic Dinacharya Tips:</strong> {'; '.join(lifestyle) if lifestyle else 'General healthy lifestyle'}</p>"
                f"</div>"
            )
            sections.append({
                "title": "AYUSH Holistic & Prakriti Assessment",
                "code": {
                    "coding": [{"system": "https://ayush.gov.in/fhir/cs/dosha", "code": "AYUSH-PRAKRITI-VIKRITI", "display": "AYUSH Holistic Assessment"}],
                    "text": "AYUSH Prakriti & Vikriti",
                },
                "text": {
                    "status": "generated",
                    "div": ayush_html,
                },
            })

        # 8. Clinical Triage Risk Stratification Section
        risk = summary.risk_assessment or {}
        if risk:
            level = risk.get("risk_level", "Low")
            score = risk.get("score", 1)
            specialty = risk.get("recommended_specialty", "General Medicine")
            red_flags = risk.get("red_flags", [])
            flags_str = ", ".join(red_flags) if red_flags else "No acute danger signs detected"

            triage_html = (
                f"<div xmlns=\"http://www.w3.org/1999/xhtml\">"
                f"<p><strong>Triage Category:</strong> {level} (Urgency Score: {score}/10)</p>"
                f"<p><strong>Routing Specialty:</strong> {specialty}</p>"
                f"<p><strong>Red Flags:</strong> {flags_str}</p>"
                f"</div>"
            )
            sections.append({
                "title": "Clinical Triage & Risk Stratification",
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": LOINC_TRIAGE, "display": "Emergency department Triage note"}],
                    "text": "Triage & Risk Score",
                },
                "text": {
                    "status": "generated",
                    "div": triage_html,
                },
            })

        return {
            "resourceType": "Composition",
            "id": composition_id,
            "status": "final",
            "type": {
                "coding": [{"system": "http://loinc.org", "code": LOINC_DOC_SUMMARY, "display": "Summary of episode note"}],
                "text": "MediKiosk OPD Clinical Consultation Summary",
            },
            "category": [{
                "coding": [{"system": "http://loinc.org", "code": "LP173255-0", "display": "Outpatient note"}],
            }],
            "subject": {
                "reference": patient_ref,
                "display": patient_display,
            },
            "date": created_at,
            "author": [{
                "reference": f"Device/{self.facility_id}",
                "display": self.organization_name,
            }],
            "title": "MediKiosk Smart OPD Clinical Intake Summary",
            "custodian": {
                "display": self.organization_name,
            },
            "section": sections,
        }

    def _build_condition_resources(
        self,
        summary: ClinicalSummaryPayload,
        patient_ref: str,
        patient_display: str,
        created_at: str,
    ) -> List[Dict[str, Any]]:
        """Construct FHIR Condition resources from ICD-10 codes and free-text diagnoses."""
        conditions: List[Dict[str, Any]] = []
        seen_codes = set()

        # Build from ICD-10 structured codes
        for item in summary.icd10_codes:
            code = item.get("code", "").strip()
            desc = item.get("description", "").strip() or code
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)

            cond_id = str(uuid.uuid4())
            conditions.append({
                "resourceType": "Condition",
                "id": cond_id,
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}],
                },
                "verificationStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "provisional", "display": "Provisional"}],
                },
                "category": [{
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}],
                }],
                "code": {
                    "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": code, "display": desc}],
                    "text": desc,
                },
                "subject": {
                    "reference": patient_ref,
                    "display": patient_display,
                },
                "recordedDate": created_at,
            })

        # Build from diagnoses list if not already covered
        for diag in summary.diagnoses:
            if not diag or diag in seen_codes:
                continue
            seen_codes.add(diag)
            cond_id = str(uuid.uuid4())
            conditions.append({
                "resourceType": "Condition",
                "id": cond_id,
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active", "display": "Active"}],
                },
                "verificationStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "provisional", "display": "Provisional"}],
                },
                "category": [{
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "encounter-diagnosis", "display": "Encounter Diagnosis"}],
                }],
                "code": {
                    "text": diag,
                },
                "subject": {
                    "reference": patient_ref,
                    "display": patient_display,
                },
                "recordedDate": created_at,
            })

        return conditions

    def _build_medication_resources(
        self,
        medications: List[Medication],
        patient_ref: str,
        patient_display: str,
        created_at: str,
    ) -> List[Dict[str, Any]]:
        """Construct FHIR MedicationStatement resources."""
        resources: List[Dict[str, Any]] = []

        for med in medications:
            med_id = str(uuid.uuid4())
            dosage_text = f"{med.dosage} {med.frequency} for {med.duration}".strip()
            item: Dict[str, Any] = {
                "resourceType": "MedicationStatement",
                "id": med_id,
                "status": "active",
                "medicationCodeableConcept": {
                    "text": med.drug_name,
                },
                "subject": {
                    "reference": patient_ref,
                    "display": patient_display,
                },
                "effectiveDateTime": created_at,
                "dosage": [{
                    "text": dosage_text,
                    "timing": {
                        "code": {"text": med.frequency},
                    },
                }],
            }
            if med.instructions:
                item["note"] = [{"text": med.instructions}]

            resources.append(item)

        return resources

    def _build_lab_observations(
        self,
        labs: List[LabResult],
        patient_ref: str,
        patient_display: str,
        created_at: str,
    ) -> List[Dict[str, Any]]:
        """Construct FHIR Observation resources for diagnostic lab test results."""
        observations: List[Dict[str, Any]] = []

        for lab in labs:
            obs_id = str(uuid.uuid4())
            obs: Dict[str, Any] = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory",
                    }],
                }],
                "code": {
                    "text": lab.test_name,
                },
                "subject": {
                    "reference": patient_ref,
                    "display": patient_display,
                },
                "effectiveDateTime": created_at,
            }

            # Parse numeric value if possible
            numeric_val = self._try_parse_float(lab.value)
            if numeric_val is not None:
                obs["valueQuantity"] = {
                    "value": numeric_val,
                    "unit": lab.unit,
                    "system": "http://unitsofmeasure.org",
                }
            else:
                obs["valueString"] = f"{lab.value} {lab.unit}".strip()

            # Interpretation (Abnormal vs Normal)
            if lab.is_abnormal:
                obs["interpretation"] = [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "A",
                        "display": "Abnormal",
                    }],
                }]
            else:
                obs["interpretation"] = [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "N",
                        "display": "Normal",
                    }],
                }]

            if lab.reference_range:
                obs["referenceRange"] = [{"text": lab.reference_range}]

            observations.append(obs)

        return observations

    def _build_vital_observations(
        self,
        vitals: Optional[VitalSigns],
        patient_ref: str,
        patient_display: str,
        created_at: str,
    ) -> List[Dict[str, Any]]:
        """Construct FHIR Observation resources for recorded physiological vitals."""
        if not vitals:
            return []

        observations: List[Dict[str, Any]] = []

        # Heart Rate
        if vitals.heart_rate is not None:
            observations.append({
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_HEART_RATE, "display": "Heart rate"}], "text": "Heart Rate"},
                "subject": {"reference": patient_ref, "display": patient_display},
                "effectiveDateTime": created_at,
                "valueQuantity": {"value": vitals.heart_rate, "unit": "/min", "system": "http://unitsofmeasure.org", "code": "/min"},
            })

        # Oxygen Saturation (SpO2)
        if vitals.spo2 is not None:
            observations.append({
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_O2_SAT, "display": "Oxygen saturation in Arterial blood"}], "text": "SpO2"},
                "subject": {"reference": patient_ref, "display": patient_display},
                "effectiveDateTime": created_at,
                "valueQuantity": {"value": vitals.spo2, "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"},
            })

        # Blood Pressure Panel (Systolic & Diastolic)
        if vitals.systolic_bp is not None or vitals.diastolic_bp is not None:
            components = []
            if vitals.systolic_bp is not None:
                components.append({
                    "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_BP_SYSTOLIC, "display": "Systolic blood pressure"}]},
                    "valueQuantity": {"value": vitals.systolic_bp, "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"},
                })
            if vitals.diastolic_bp is not None:
                components.append({
                    "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_BP_DIASTOLIC, "display": "Diastolic blood pressure"}]},
                    "valueQuantity": {"value": vitals.diastolic_bp, "unit": "mm[Hg]", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"},
                })

            observations.append({
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_BP_PANEL, "display": "Blood pressure panel with all children optional"}], "text": "Blood Pressure"},
                "subject": {"reference": patient_ref, "display": patient_display},
                "effectiveDateTime": created_at,
                "component": components,
            })

        # Body Temperature
        if vitals.temperature_f is not None:
            observations.append({
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_BODY_TEMP, "display": "Body temperature"}], "text": "Body Temperature"},
                "subject": {"reference": patient_ref, "display": patient_display},
                "effectiveDateTime": created_at,
                "valueQuantity": {"value": vitals.temperature_f, "unit": "[degF]", "system": "http://unitsofmeasure.org", "code": "[degF]"},
            })

        # Respiratory Rate
        if vitals.respiratory_rate is not None:
            observations.append({
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs", "display": "Vital Signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": LOINC_RESP_RATE, "display": "Respiratory rate"}], "text": "Respiratory Rate"},
                "subject": {"reference": patient_ref, "display": patient_display},
                "effectiveDateTime": created_at,
                "valueQuantity": {"value": vitals.respiratory_rate, "unit": "/min", "system": "http://unitsofmeasure.org", "code": "/min"},
            })

        return observations

    # -----------------------------------------------------------------
    # Parsers and Normalizers
    # -----------------------------------------------------------------

    @staticmethod
    def _try_parse_float(val: Any) -> Optional[float]:
        """Safely extract float from numeric string or float."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = re.sub(r"[^\d.]", "", str(val))
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _normalize_profile(
        cls,
        profile_input: Optional[Union[ABHAProfile, Dict[str, Any]]],
        fallback_demographics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract a standard profile dictionary."""
        if isinstance(profile_input, ABHAProfile):
            return profile_input.model_dump()
        if isinstance(profile_input, dict) and profile_input:
            return profile_input

        # Fallback to demographics provided in summary
        fb = fallback_demographics or {}
        return {
            "abha_number": fb.get("abha_number", "14-8921-3456-7890"),
            "abha_address": fb.get("abha_address", "ramesh.kumar@abdm"),
            "name": fb.get("name", "Ramesh Kumar"),
            "gender": fb.get("gender", "M"),
            "dob": fb.get("dob", "1965-04-12"),
            "mobile": fb.get("mobile", "+91-98765-43210"),
            "address": {
                "line": "Ward 4, Civil Lines",
                "district": "Jaipur",
                "state": "Rajasthan",
                "pincode": "302001",
            },
        }

    @classmethod
    def _dict_to_summary_payload(cls, data: Dict[str, Any]) -> ClinicalSummaryPayload:
        """Coerce raw dictionary (combining OCR + LLM summary) into ClinicalSummaryPayload."""
        meds = []
        for m in data.get("medications", []):
            if isinstance(m, Medication):
                meds.append(m)
            elif isinstance(m, dict):
                meds.append(Medication(
                    drug_name=m.get("drug_name") or m.get("name", "Unknown Medicine"),
                    dosage=m.get("dosage", "1 dose"),
                    frequency=m.get("frequency", "OD"),
                    duration=m.get("duration", "5 days"),
                    instructions=m.get("instructions"),
                ))

        labs = []
        for lb in data.get("lab_results", []):
            if isinstance(lb, LabResult):
                labs.append(lb)
            elif isinstance(lb, dict):
                labs.append(LabResult(
                    test_name=lb.get("test_name") or lb.get("test", "Diagnostic Test"),
                    value=str(lb.get("value", "")),
                    unit=lb.get("unit", ""),
                    is_abnormal=bool(lb.get("is_abnormal", False)),
                    reference_range=lb.get("reference_range"),
                ))

        # Handle vitals
        vitals_dict = data.get("vitals", {})
        vitals_obj = VitalSigns(**vitals_dict) if isinstance(vitals_dict, dict) else None

        # Handle ayush notes
        ayush_dict = data.get("ayush_notes", {})
        ayush_obj = AyushAssessment(**ayush_dict) if isinstance(ayush_dict, dict) else None

        # Handle icd10 codes
        raw_icd = data.get("icd10_codes", [])
        icd_codes = []
        for c in raw_icd:
            if isinstance(c, dict):
                icd_codes.append(c)
            elif hasattr(c, "model_dump"):
                icd_codes.append(c.model_dump())

        return ClinicalSummaryPayload(
            patient_id=data.get("patient_id"),
            patient_demographics=data.get("patient_demographics", {}),
            chief_complaints=data.get("chief_complaints", []),
            patient_symptoms=data.get("patient_symptoms", []),
            medical_history_summary=data.get("medical_history_summary", ""),
            diagnoses=data.get("diagnoses", []),
            icd10_codes=icd_codes,
            medications=meds,
            lab_results=labs,
            vitals=vitals_obj,
            ayush_notes=ayush_obj,
            risk_assessment=data.get("risk_assessment", {}),
            voice_transcript=data.get("voice_transcript"),
        )


# Singleton converter instance
converter = FHIRConverter()


def convert_to_fhir_bundle(
    summary_payload: Union[ClinicalSummaryPayload, Dict[str, Any]],
    abha_profile: Optional[Union[ABHAProfile, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Top-level convenience function to export to HL7 FHIR R4 Document Bundle."""
    return converter.convert_to_fhir_bundle(summary_payload, abha_profile)

