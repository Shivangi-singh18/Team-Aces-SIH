"""Unit tests for MedicalDocumentSchema and related models."""

import json
import unittest
from pydantic import ValidationError

from module_b_ocr.schemas import LabResult, MedicalDocumentSchema, Medication


class TestMedicalSchemas(unittest.TestCase):
    def test_medication_model(self):
        med = Medication(
            drug_name="Paracetamol",
            dosage="650 mg",
            frequency="1-0-1",
            duration="5 days",
        )
        self.assertEqual(med.drug_name, "Paracetamol")
        self.assertEqual(med.dosage, "650 mg")
        self.assertEqual(med.frequency, "1-0-1")
        self.assertEqual(med.duration, "5 days")

    def test_lab_result_model(self):
        lab = LabResult(
            test_name="Hemoglobin",
            value="10.5",
            unit="g/dL",
            is_abnormal=True,
        )
        self.assertEqual(lab.test_name, "Hemoglobin")
        self.assertEqual(lab.value, "10.5")
        self.assertEqual(lab.unit, "g/dL")
        self.assertTrue(lab.is_abnormal)

    def test_medical_document_schema_defaults(self):
        doc = MedicalDocumentSchema()
        self.assertEqual(doc.document_type, "unknown")
        self.assertEqual(doc.diagnoses, [])
        self.assertEqual(doc.medications, [])
        self.assertEqual(doc.lab_results, [])
        self.assertEqual(doc.unparsed_text, "")

    def test_serialization_roundtrip(self):
        doc = MedicalDocumentSchema(
            document_type="prescription",
            diagnoses=["Viral Bronchitis", "Hypertension"],
            medications=[
                Medication(
                    drug_name="Augmentin",
                    dosage="625 mg",
                    frequency="1-0-1",
                    duration="7 days",
                )
            ],
            lab_results=[
                LabResult(
                    test_name="WBC",
                    value="11500",
                    unit="/cumm",
                    is_abnormal=True,
                )
            ],
            unparsed_text="Review in 1 week.",
        )

        d = doc.to_dict()
        self.assertEqual(d["document_type"], "prescription")
        self.assertEqual(len(d["medications"]), 1)
        self.assertEqual(d["medications"][0]["drug_name"], "Augmentin")

        json_str = doc.to_json()
        loaded = MedicalDocumentSchema.from_json(json_str)
        self.assertEqual(loaded.document_type, "prescription")
        self.assertEqual(loaded.diagnoses, ["Viral Bronchitis", "Hypertension"])
        self.assertEqual(loaded.medications[0].dosage, "625 mg")
        self.assertTrue(loaded.lab_results[0].is_abnormal)

    def test_schema_validation_error(self):
        with self.assertRaises(ValidationError):
            # Missing required field 'is_abnormal'
            LabResult(test_name="Hb", value="12", unit="g/dL")  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
