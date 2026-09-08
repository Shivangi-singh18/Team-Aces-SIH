"""Clinical Entity Extraction and Structuring Module (Module B - MediKiosk).

Parses raw OCR output into strictly-typed MedicalDocumentSchema using LLM structured outputs
(Gemini, OpenAI) with a robust rule-based regex fallback for Indian OPD prescriptions.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from .schemas import LabResult, MedicalDocumentSchema, Medication

logger = logging.getLogger(__name__)

CLINICAL_EXTRACTION_SYSTEM_PROMPT = """You are an expert Clinical Informatics AI specialized in Indian Outpatient Department (OPD) medical documents, doctor prescriptions, pathology reports, and discharge summaries.

Your task is to analyze raw OCR text from a medical document and extract clinical entities into a strictly structured format conforming to the requested schema:

1. document_type: Identify whether the document is:
   - "prescription": Doctor prescription slips, OPD consultation cards, Rx slips.
   - "lab_report": Pathology, biochemistry, hematology, or diagnostic investigation reports.
   - "discharge_summary": Inpatient hospital discharge summaries.
   - "unknown": Cannot be determined.

2. diagnoses: Extract all clinical diagnoses, impressions, provisional diagnoses, or presenting chief complaints (e.g., "Type 2 Diabetes Mellitus", "Acute Bronchitis", "Fever with chills", "Hypertension").

3. medications: For each prescribed medication, extract:
   - drug_name: Brand or generic name (e.g., "Paracetamol", "Tab. Pantop 40", "Augmentin", "Telmisartan").
   - dosage: Strength/dosage (e.g., "500 mg", "40 mg", "1 tablet", "5 ml").
   - frequency: Dosage timing/schedule. Normalize Indian OPD shorthand if present:
     * "1-0-1" -> "Twice daily (Morning & Night)" or "1-0-1"
     * "1-0-0" -> "Once daily (Morning)"
     * "0-0-1" -> "Once daily (Night / Bedtime)"
     * "1-1-1" -> "Three times daily (TDS)"
     * "OD", "BD", "TDS", "QID", "SOS" (as needed), "Stat".
   - duration: Number of days/weeks (e.g., "5 days", "1 month", "2 weeks", "SOS").

4. lab_results: For lab reports, extract individual test parameters:
   - test_name: E.g., "Hemoglobin", "Fasting Blood Sugar", "Serum Creatinine", "HbA1c".
   - value: Test value as observed (e.g., "11.2", "142", "Positive").
   - unit: Measurement unit (e.g., "g/dL", "mg/dL", "%", "mmol/L").
   - is_abnormal: Boolean (true if value is outside the reference range or marked with High/Low/*, otherwise false).

5. unparsed_text: Any residual text such as hospital name, doctor details, date, instructions, or non-medical notes.

Be accurate and never hallucinate clinical entities not mentioned in the OCR text.
"""


class GeminiEntityExtractor:
    """Extracts clinical entities using Google Gemini Structured Outputs."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def extract(self, raw_text: str) -> MedicalDocumentSchema:
        """Call Gemini API with structured response schema."""
        try:
            # First try google-genai SDK
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            prompt = f"{CLINICAL_EXTRACTION_SYSTEM_PROMPT}\n\n=== RAW OCR TEXT ===\n{raw_text}"

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=MedicalDocumentSchema,
                    temperature=0.1,
                ),
            )
            return MedicalDocumentSchema.model_validate_json(response.text)
        except ImportError:
            # Fallback to google-generativeai legacy package if installed
            import google.generativeai as legacy_genai

            legacy_genai.configure(api_key=self.api_key)
            model = legacy_genai.GenerativeModel(
                model_name=self.model,
                generation_config={"response_mime_type": "application/json"},
                system_instruction=CLINICAL_EXTRACTION_SYSTEM_PROMPT,
            )
            response = model.generate_content(
                f"Extract structured clinical data conforming to MedicalDocumentSchema schema:\n{raw_text}"
            )
            return MedicalDocumentSchema.model_validate_json(response.text)


class OpenAIEntityExtractor:
    """Extracts clinical entities using OpenAI Structured Outputs."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def extract(self, raw_text: str) -> MedicalDocumentSchema:
        """Call OpenAI structured outputs endpoint."""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        completion = client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": CLINICAL_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"=== RAW OCR TEXT ===\n{raw_text}"},
            ],
            response_format=MedicalDocumentSchema,
            temperature=0.1,
        )
        message = completion.choices[0].message
        if message.parsed:
            return message.parsed
        return MedicalDocumentSchema.model_validate_json(message.content or "{}")


class HeuristicRuleBasedExtractor:
    """Deterministic, regex & clinical lexicon-based extractor.

    Acts as an offline fallback when no LLM API keys are provided.
    Specially tuned for Indian OPD prescription conventions and pathology reports.
    """

    # Common Indian OPD medications
    COMMON_DRUGS = [
        "Paracetamol", "Dolo", "Calpol", "Crocin", "Pantop", "Pantoprazole", "Pan-D",
        "Omeprazole", "Rabeprazole", "Rablet", "Amoxicillin", "Augmentin", "Moxikind",
        "Azithromycin", "Azee", "Cefixime", "Taxim-O", "Ciprofloxacin", "Ofloxacin",
        "Metformin", "Glycomet", "Glimepiride", "Telmisartan", "Telma", "Amlodipine",
        "Amlong", "Atorvastatin", "Atorva", "Rosuvastatin", "Montelukast", "Montair-LC",
        "Cetirizine", "Levocetirizine", "Cetzine", "Allegra", "Fexofenadine", "ORS",
        "Electral", "Combiflam", "Ibuprofen", "Aceclofenac", "Zerodol-SP", "Tramadol",
        "Domperidone", "Vomikind", "Ondansetron", "Emset", "Ranitidine", "Aciloc",
    ]

    # Common lab parameters and standard reference bounds
    COMMON_LAB_TESTS = {
        "hemoglobin": {"unit": "g/dL", "low": 12.0, "high": 17.5},
        "hb": {"unit": "g/dL", "low": 12.0, "high": 17.5},
        "fasting blood sugar": {"unit": "mg/dL", "low": 70.0, "high": 100.0},
        "fbs": {"unit": "mg/dL", "low": 70.0, "high": 100.0},
        "post prandial blood sugar": {"unit": "mg/dL", "low": 90.0, "high": 140.0},
        "ppbs": {"unit": "mg/dL", "low": 90.0, "high": 140.0},
        "random blood sugar": {"unit": "mg/dL", "low": 70.0, "high": 140.0},
        "rbs": {"unit": "mg/dL", "low": 70.0, "high": 140.0},
        "hba1c": {"unit": "%", "low": 4.0, "high": 5.6},
        "serum creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.2},
        "creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.2},
        "blood urea": {"unit": "mg/dL", "low": 15.0, "high": 45.0},
        "urea": {"unit": "mg/dL", "low": 15.0, "high": 45.0},
        "total leukocyte count": {"unit": "/cumm", "low": 4000.0, "high": 11000.0},
        "wbc": {"unit": "/cumm", "low": 4000.0, "high": 11000.0},
        "platelet count": {"unit": "lakhs/cumm", "low": 1.5, "high": 4.5},
        "platelets": {"unit": "lakhs/cumm", "low": 1.5, "high": 4.5},
        "sgpt": {"unit": "U/L", "low": 7.0, "high": 56.0},
        "sgot": {"unit": "U/L", "low": 10.0, "high": 40.0},
        "serum bilirubin": {"unit": "mg/dL", "low": 0.2, "high": 1.2},
        "total bilirubin": {"unit": "mg/dL", "low": 0.2, "high": 1.2},
        "uric acid": {"unit": "mg/dL", "low": 3.5, "high": 7.2},
        "cholesterol": {"unit": "mg/dL", "low": 125.0, "high": 200.0},
        "tsh": {"unit": "uIU/mL", "low": 0.4, "high": 4.5},
    }

    def extract(self, raw_text: str) -> MedicalDocumentSchema:
        """Extract structured medical information via heuristics."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        lower_text = raw_text.lower()

        # 1. Determine document type
        doc_type: str = "unknown"
        if any(kw in lower_text for kw in ["discharge summary", "discharge card", "admission date", "date of discharge"]):
            doc_type = "discharge_summary"
        elif any(kw in lower_text for kw in ["lab report", "pathology", "biochemistry", "hematology", "investigation report", "sample received", "reference range"]):
            doc_type = "lab_report"
        elif any(kw in lower_text for kw in ["rx", "prescription", "opd card", "doctor", "clinic", "hospital", "patient", "tab.", "cap.", "syp.", "1-0-1", "od", "bd", "tds"]):
            doc_type = "prescription"

        # 2. Extract diagnoses
        diagnoses = self._extract_diagnoses(lines, raw_text)

        # 3. Extract medications
        medications = self._extract_medications(lines)

        # 4. Extract lab results
        lab_results = self._extract_lab_results(lines)

        # 5. Gather unparsed text
        unparsed = self._extract_unparsed(lines)

        return MedicalDocumentSchema(
            document_type=doc_type,  # type: ignore[arg-type]
            diagnoses=diagnoses,
            medications=medications,
            lab_results=lab_results,
            unparsed_text=unparsed,
        )

    def _extract_diagnoses(self, lines: List[str], full_text: str) -> List[str]:
        diagnoses: List[str] = []
        diag_patterns = [
            r"(?:dx|diagnosis|provisional diagnosis|impression|c/o|complaints|known case of)[:\s\-]+([^\n\r,;.]+)",
            r"(?:history of|diagnosed with)[:\s\-]+([^\n\r,;.]+)",
        ]
        for pattern in diag_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for m in matches:
                val = m.group(1).strip()
                if len(val) > 2 and val.lower() not in [d.lower() for d in diagnoses]:
                    diagnoses.append(val)

        # Common clinical conditions heuristic check
        conditions = [
            "Type 2 Diabetes Mellitus", "Hypertension", "Acute Bronchitis",
            "Urinary Tract Infection", "Gastroenteritis", "Pyrexia of Unknown Origin",
            "Viral Fever", "Dengue", "Malaria", "Migraine", "Asthma",
            "Upper Respiratory Tract Infection", "Hypothyroidism",
        ]
        for c in conditions:
            if re.search(rf"\b{re.escape(c)}\b", full_text, re.IGNORECASE):
                if c not in diagnoses:
                    diagnoses.append(c)

        return diagnoses

    def _extract_medications(self, lines: List[str]) -> List[Medication]:
        medications: List[Medication] = []
        # Pattern for frequency: 1-0-1, 1-1-1, 1-0-0, 0-0-1, OD, BD, TDS, QID, SOS, HS
        freq_pattern = r"(?:(?:[012]-[012]-[012](?:-[012])?)|(?:once|twice|thrice)\s+daily|OD|BD|BID|TDS|TID|QID|SOS|HS|PRN)"
        dosage_pattern = r"(?:\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|tab|cap|pills?|units?))"
        duration_pattern = r"(?:\d+\s*(?:days?|weeks?|months?))"

        for line in lines:
            line_clean = line.strip()
            # Check if line looks like a drug line: begins with Tab/Cap/Syp or contains known drug
            is_drug_line = bool(
                re.match(r"^(?:tab(?:let)?\.?|cap(?:sule)?\.?|syp(?:rup)?\.?|inj(?:ection)?\.?|ointment)\b", line_clean, re.IGNORECASE)
                or any(d.lower() in line_clean.lower() for d in self.COMMON_DRUGS)
            )

            if not is_drug_line:
                continue

            # Extract drug name
            name = line_clean
            # Remove leading numbering/bullets like "1.", "1)", "-", "*"
            name = re.sub(r"^[\d\.\)\-\*\s]+", "", name).strip()
            # Remove Tab./Cap./Syp./Inj. prefix
            name = re.sub(r"^(?:tab(?:let)?\.?|cap(?:sule)?\.?|syp(?:rup)?\.?|inj(?:ection)?\.?)\s+", "", name, flags=re.IGNORECASE).strip()

            # Find dosage
            dosage_match = re.search(dosage_pattern, name, re.IGNORECASE)
            dosage = dosage_match.group(0).strip() if dosage_match else "As directed"

            # Find frequency
            freq_match = re.search(freq_pattern, name, re.IGNORECASE) or re.search(freq_pattern, line_clean, re.IGNORECASE)
            frequency = freq_match.group(0).strip() if freq_match else "1-0-1"

            # Find duration
            dur_match = re.search(duration_pattern, name, re.IGNORECASE) or re.search(duration_pattern, line_clean, re.IGNORECASE)
            duration = dur_match.group(0).strip() if dur_match else "5 days"

            # Clean name up to dosage or frequency or duration
            name_freq_match = re.search(freq_pattern, name, re.IGNORECASE)
            if dosage_match:
                name = name[: dosage_match.start()].strip()
            elif name_freq_match:
                name = name[: name_freq_match.start()].strip()
            elif re.search(duration_pattern, name, re.IGNORECASE):
                name = name[: re.search(duration_pattern, name, re.IGNORECASE).start()].strip()

            # Clean punctuation
            name = re.sub(r"[\-–:]+$", "", name).strip()
            if not name:
                name = line_clean.split()[0]

            medications.append(
                Medication(
                    drug_name=name,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                )
            )
        return medications

    def _extract_lab_results(self, lines: List[str]) -> List[LabResult]:
        lab_results: List[LabResult] = []

        for line in lines:
            lower_line = line.lower()
            for test_name, meta in self.COMMON_LAB_TESTS.items():
                pattern = rf"\b{re.escape(test_name)}\b[:\s\-–]+([\d]+(?:\.[\d]+)?)\s*([a-zA-Z/%]*)"
                m = re.search(pattern, lower_line)
                if m:
                    val_str = m.group(1)
                    matched_unit = m.group(2).strip()
                    if matched_unit and matched_unit.lower() == meta["unit"].lower():
                        unit_str = meta["unit"]
                    elif matched_unit:
                        unit_str = matched_unit
                    else:
                        unit_str = meta["unit"]
                    try:
                        num_val = float(val_str)
                        is_abnormal = (num_val < meta["low"]) or (num_val > meta["high"])
                    except ValueError:
                        is_abnormal = False

                    # Check if text explicitly says High / Low / *
                    if any(flag in line for flag in ["(H)", "(L)", "*", "High", "Low", "ABNORMAL"]):
                        is_abnormal = True

                    # Format clean test name
                    display_name = test_name.title()
                    if test_name in ["hb", "wbc", "fbs", "ppbs", "rbs", "hba1c", "sgpt", "sgot", "tsh"]:
                        display_name = test_name.upper()

                    # Avoid duplicate test additions
                    if not any(r.test_name.lower() == display_name.lower() for r in lab_results):
                        lab_results.append(
                            LabResult(
                                test_name=display_name,
                                value=val_str,
                                unit=unit_str,
                                is_abnormal=is_abnormal,
                            )
                        )
                    break
        return lab_results

    def _extract_unparsed(self, lines: List[str]) -> str:
        """Collect residual lines not easily categorized into main entities."""
        unparsed_lines: List[str] = []
        for line in lines:
            lower = line.lower()
            if any(h in lower for h in ["hospital", "clinic", "dr.", "doctor", "date:", "reg no", "age:", "gender:"]):
                unparsed_lines.append(line)
        return "\n".join(unparsed_lines[:5]).strip()


class ClinicalEntityExtractor:
    """Main orchestrator for clinical entity extraction with multi-provider fallbacks."""

    def __init__(self) -> None:
        self.gemini = GeminiEntityExtractor()
        self.openai = OpenAIEntityExtractor()
        self.heuristic = HeuristicRuleBasedExtractor()

    def extract(self, raw_text: str, provider: str = "auto") -> MedicalDocumentSchema:
        """Extract clinical entities into structured MedicalDocumentSchema.

        Args:
            raw_text: Text string returned from OCR engine.
            provider: 'auto', 'gemini', 'openai', or 'heuristic'.

        Returns:
            Validated MedicalDocumentSchema instance.
        """
        if not raw_text or not raw_text.strip():
            return MedicalDocumentSchema(document_type="unknown", unparsed_text="")

        provider_norm = provider.lower().strip()

        if provider_norm == "gemini":
            if self.gemini.is_available():
                return self.gemini.extract(raw_text)
            raise RuntimeError("Gemini API key not found in environment (GEMINI_API_KEY).")

        if provider_norm == "openai":
            if self.openai.is_available():
                return self.openai.extract(raw_text)
            raise RuntimeError("OpenAI API key not found in environment (OPENAI_API_KEY).")

        if provider_norm == "heuristic":
            return self.heuristic.extract(raw_text)

        # Provider 'auto' orchestration:
        # 1. Try Gemini (fast, cost-effective structured output)
        if self.gemini.is_available():
            try:
                return self.gemini.extract(raw_text)
            except Exception as e:
                logger.warning(f"Gemini entity extraction failed: {e}. Attempting next provider.")

        # 2. Try OpenAI
        if self.openai.is_available():
            try:
                return self.openai.extract(raw_text)
            except Exception as e:
                logger.warning(f"OpenAI entity extraction failed: {e}. Falling back to heuristics.")

        # 3. Deterministic rule-based heuristic extraction fallback
        return self.heuristic.extract(raw_text)


_default_entity_extractor = ClinicalEntityExtractor()


def extract_clinical_entities(raw_text: str, provider: str = "auto") -> MedicalDocumentSchema:
    """Wrapper function to parse raw medical text into typed MedicalDocumentSchema.

    Args:
        raw_text: Raw OCR transcription.
        provider: Extraction provider ('auto', 'gemini', 'openai', 'heuristic').

    Returns:
        MedicalDocumentSchema conforming to the MediKiosk data contract.
    """
    return _default_entity_extractor.extract(raw_text, provider=provider)
