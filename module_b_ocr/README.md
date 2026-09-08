# Module B: Medical Document Digitization Pipeline (`module_b_ocr`)

> Part of **MediKiosk** — Patient Case-Taking Software for Indian OPDs.

This module is a standalone, isolated medical document digitization and clinical entity extraction service. It ingests images of doctor prescriptions, pathology/lab reports, and discharge summaries, extracts the text using a dual OCR engine (printed vs. handwritten), and structures the data into a strictly-typed JSON payload.

---

## 🏗️ Architecture & Pipeline Flow

```
[ Medical Document Image ]
 (Path, Base64, Bytes, Stream)
               │
               ▼
   [ Image Preprocessor ]
 (EXIF Rotation, Auto-Contrast, Grayscale, Denoising)
               │
               ▼
      [ Dual OCR Engine ]
  ┌──────────────────────────┴──────────────────────────┐
  ▼                                                     ▼
[ Printed & Regional Docs ]               [ Handwritten Prescriptions ]
 • Google Cloud Vision API                 • Microsoft TrOCR (Transformers)
 • Azure Document Intelligence (Fallback)  • EasyOCR (Medical Layout Tuned)
  └──────────────────────────┬──────────────────────────┘
                             │
                      Raw OCR String
                             │
                             ▼
              [ Clinical Entity Extractor ]
  ┌──────────────────────────┴──────────────────────────┐
  ▼                                                     ▼
[ LLM Structured Parsers ]                [ Indian OPD Heuristics Fallback ]
 • Google Gemini (JSON Schema Mode)        • Prescription Regex (1-0-1, OD, BD)
 • OpenAI (Pydantic Structured Outputs)    • Common Indian Brands & Dosages
                                           • Lab Test Bounds (Hb, FBS, etc.)
  └──────────────────────────┬──────────────────────────┘
                             │
                             ▼
                [ MedicalDocumentSchema ]
                  (Validated JSON Output)
```

---

## 📋 Data Contract & Output Schema

The pipeline returns a strictly typed Pydantic object conforming to this specification:

```json
{
  "document_type": "prescription | lab_report | discharge_summary | unknown",
  "diagnoses": [
    "string"
  ],
  "medications": [
    {
      "drug_name": "string",
      "dosage": "string",
      "frequency": "string",
      "duration": "string"
    }
  ],
  "lab_results": [
    {
      "test_name": "string",
      "value": "string",
      "unit": "string",
      "is_abnormal": true
    }
  ],
  "unparsed_text": "string"
}
```

---

## 🚀 Quickstart for Teammates

### 1. Installation
Inside the repository root or venv:
```bash
pip install -r module_b_ocr/requirements.txt
```

### 2. Python Integration Example
```python
from module_b_ocr import process_medical_document

# Ingest from file path, raw bytes, or base64 string
result = process_medical_document("path/to/prescription.jpg")

print(f"Document Type: {result.document_type}")
print(f"Diagnoses: {result.diagnoses}")

for med in result.medications:
    print(f"Rx: {med.drug_name} | Dose: {med.dosage} | Freq: {med.frequency} | Dur: {med.duration}")

for lab in result.lab_results:
    flag = "ABNORMAL" if lab.is_abnormal else "Normal"
    print(f"Test: {lab.test_name}: {lab.value} {lab.unit} [{flag}]")

# Export to dictionary or JSON string
json_payload = result.to_json(indent=2)
dict_payload = result.to_dict()
```

### 3. CLI Usage
```bash
# Test on any image
python -m module_b_ocr.cli path/to/prescription.jpg --output result.json

# Test synthetic OPD prescription (dry-run without needing an image file)
python -m module_b_ocr.cli --mock-sample prescription

# Test synthetic pathology report
python -m module_b_ocr.cli --mock-sample lab_report
```

---

## 🔑 Environment Configuration

Set any of the following environment variables depending on your deployment target:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for structured clinical entity extraction. |
| `OPENAI_API_KEY` | OpenAI API key (alternative LLM structured output provider). |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account JSON for Google Cloud Vision OCR. |
| `AZURE_VISION_KEY` & `AZURE_VISION_ENDPOINT` | Azure Computer Vision / Document Intelligence credentials (optional fallback). |

> **Offline / No-Key Mode:** If no external keys are configured, the system gracefully falls back to the deterministic Indian OPD heuristic engine so local tests, CI pipelines, and offline demonstrations never crash.

---

## 🧪 Testing

Run the test suite:
```bash
python -m unittest discover -s module_b_ocr/tests -p "test_*.py"
```
