"""Unit tests for ClinicalEntityExtractor and HeuristicRuleBasedExtractor."""

import unittest
from unittest.mock import MagicMock

from module_b_ocr.entity_extractor import (
    ClinicalEntityExtractor,
    HeuristicRuleBasedExtractor,
    extract_clinical_entities,
)
from module_b_ocr.schemas import MedicalDocumentSchema


class TestEntityExtractor(unittest.TestCase):
    def setUp(self):
        self.heuristic = HeuristicRuleBasedExtractor()

    def test_prescription_extraction_heuristic(self):
        raw_prescription = """
        CITY HOSPITAL & OPD CLINIC
        Dr. S. K. Gupta, MBBS, MD
        Date: 08-09-2026
        Patient: Ramesh Chandra, 48 Y / M
        Diagnosis: Upper Respiratory Tract Infection, Viral Fever
        Rx:
        1. Tab. Paracetamol 650mg - 1-0-1 - 5 days
        2. Tab. Augmentin 625mg - 1-0-1 - 5 days
        3. Tab. Pantop 40mg - 1-0-0 - 5 days
        4. Tab. Montair-LC - 0-0-1 - 7 days
        Advice: Drink plenty of warm fluids.
        """

        result = self.heuristic.extract(raw_prescription)
        self.assertEqual(result.document_type, "prescription")

        # Check diagnoses
        self.assertTrue(
            any("respiratory" in d.lower() or "fever" in d.lower() for d in result.diagnoses),
            f"Diagnoses found: {result.diagnoses}",
        )

        # Check medications
        self.assertGreaterEqual(len(result.medications), 3)
        drug_names = [m.drug_name.lower() for m in result.medications]
        self.assertTrue(any("paracetamol" in d for d in drug_names))
        self.assertTrue(any("augmentin" in d for d in drug_names))
        self.assertTrue(any("pantop" in d for d in drug_names))

        # Check fields of one medication
        para_med = next(m for m in result.medications if "paracetamol" in m.drug_name.lower())
        self.assertIn("650mg", para_med.dosage.replace(" ", "").lower())
        self.assertIn("1-0-1", para_med.frequency)
        self.assertIn("5 days", para_med.duration)

    def test_lab_report_extraction_heuristic(self):
        raw_lab_report = """
        METROPOLIS PATHOLOGY & LAB REPORT
        Patient: Sunita Sharma, Age: 52 Y / F
        Ref Doctor: Dr. Verma

        Test Name                 Observed Value   Units    Reference Range
        Hemoglobin                9.5              g/dL     12.0 - 15.5 (Low)
        Fasting Blood Sugar       165              mg/dL    70 - 100    (High)
        HbA1c                     8.2              %        < 5.7       (High)
        Serum Creatinine          0.9              mg/dL    0.6 - 1.2   Normal
        Total Leukocyte Count     12800            /cumm    4000-11000  (High)
        """

        result = self.heuristic.extract(raw_lab_report)
        self.assertEqual(result.document_type, "lab_report")
        self.assertGreaterEqual(len(result.lab_results), 3)

        tests_map = {r.test_name.lower(): r for r in result.lab_results}
        self.assertIn("hemoglobin", tests_map)
        hb = tests_map["hemoglobin"]
        self.assertEqual(hb.value, "9.5")
        self.assertEqual(hb.unit, "g/dL")
        self.assertTrue(hb.is_abnormal)  # 9.5 is below normal (low)

        self.assertIn("fasting blood sugar", tests_map)
        fbs = tests_map["fasting blood sugar"]
        self.assertEqual(fbs.value, "165")
        self.assertTrue(fbs.is_abnormal)  # 165 is above normal

        self.assertIn("serum creatinine", tests_map)
        creat = tests_map["serum creatinine"]
        self.assertEqual(creat.value, "0.9")
        self.assertFalse(creat.is_abnormal)  # 0.9 is normal

    def test_mocked_gemini_extractor(self):
        mock_gemini = MagicMock()
        mock_gemini.is_available.return_value = True
        mock_gemini.extract.return_value = MedicalDocumentSchema(
            document_type="prescription",
            diagnoses=["Acute Pharyngitis"],
            medications=[],
            lab_results=[],
            unparsed_text="",
        )

        extractor = ClinicalEntityExtractor()
        extractor.gemini = mock_gemini

        res = extractor.extract("some raw text", provider="gemini")
        self.assertEqual(res.document_type, "prescription")
        self.assertEqual(res.diagnoses, ["Acute Pharyngitis"])
        mock_gemini.extract.assert_called_once()

    def test_auto_fallback_wrapper(self):
        # Empty text should return clean unknown document without error
        res = extract_clinical_entities("")
        self.assertEqual(res.document_type, "unknown")


if __name__ == "__main__":
    unittest.main()
