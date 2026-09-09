# MediKiosk LLM Orchestration Engine (SIH26047)
## Mobile App & Kiosk Integration API Guide

Welcome to the **MediKiosk LLM Orchestration Engine** (`module_llm_engine`), the centralized clinical intelligence backend for Project MediKiosk.

This engine synthesizes patient voice transcripts (Module A), digitized prescription and lab reports (Module B OCR), and patient demographics to produce clinical triage summaries, ICD-10 coding, clinical risk stratification, and patient-friendly instructions.

---

## 1. Quick Start & Server Launch

### Prerequisites & Installation
```bash
# Navigate to repository root
cd Team-Aces-SIH

# Install dependencies
pip install -r module_llm_engine/requirements.txt
```

### Launch the Microservice
```bash
# Start server on 0.0.0.0:8000 with auto-reload
python -m uvicorn module_llm_engine.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Zero-API-Key Offline Mock Mode is Active by Default!**
> You can develop and test your mobile application screens immediately without configuring any API keys or spending cloud credits. The engine includes deterministic clinical knowledge rules that parse symptoms, lab values, and medication allergies automatically.

### Optional Cloud LLM Configuration (`.env`)
If you want to enable live cloud LLM inference:
```env
# Primary Engine: Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Secondary Fallback Engine: OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Force Mock Mode (set to 'true' to simulate offline kiosk behavior)
MEDIKIOSK_MOCK_MODE=false
```

---

## 2. Network & Base URL Setup for Mobile Development

| Platform / Environment | Base URL | Note |
|---|---|---|
| **Production Cloud (Render)** | `https://team-aces-sih.onrender.com` | Deployed live backend (Auto-SSL) |
| **Android Studio Emulator** | `http://10.0.2.2:8000` | Android loopback to local machine |
| **iOS Simulator** | `http://localhost:8000` | Shares macOS localhost network |
| **Physical Phone (Wi-Fi)** | `http://<YOUR_PC_IP>:8000` | Phone and PC must be on same Wi-Fi |
| **Web Browser / Kiosk** | `https://team-aces-sih.onrender.com` | Production live endpoint (or `http://localhost:8000` locally) |

*CORS policy is pre-configured with `allow_origins=["*"]` to ensure zero network friction.*

---

## 3. API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check & active provider status |
| `GET` | `/api/v1/llm/providers` | Inspect configured AI models & fallback status |
| `POST` | `/api/v1/llm/process` | **Primary Intake Endpoint**: Process voice + OCR + demographics |

---

## 4. Primary Endpoint: `POST /api/v1/llm/process`

### Request Payloads

#### Scenario A: Full Combined Input (Voice + Module B OCR + Demographics)
```json
{
  "voice_transcript": "I have had severe chest pain radiating to my left arm and breathlessness for the past two hours.",
  "ocr_data": {
    "document_type": "prescription",
    "diagnoses": ["Hypertension"],
    "medications": [
      {
        "drug_name": "Amlodipine",
        "dosage": "5mg",
        "frequency": "1-0-0",
        "duration": "30 days"
      }
    ],
    "lab_results": [
      {
        "test_name": "Fasting Blood Sugar",
        "value": "280",
        "unit": "mg/dL",
        "is_abnormal": true
      }
    ],
    "unparsed_text": "BP: 165/100 mmHg"
  },
  "patient_demographics": {
    "age": 62,
    "gender": "Male",
    "known_allergies": ["Penicillin"]
  }
}
```

#### Scenario B: Voice Transcript Only (Mobile Mic Recording)
```json
{
  "voice_transcript": "I have a high fever with chills and a very bad dry cough since yesterday."
}
```

#### Scenario C: OCR Document Only (Prescription or Lab Photo Scan)
```json
{
  "ocr_data": {
    "document_type": "lab_report",
    "diagnoses": ["Type 2 Diabetes"],
    "medications": [],
    "lab_results": [
      {
        "test_name": "Hemoglobin",
        "value": "8.1",
        "unit": "g/dL",
        "is_abnormal": true
      }
    ],
    "unparsed_text": ""
  },
  "patient_demographics": {
    "age": 45,
    "gender": "Female"
  }
}
```

---

### Response Object Schema (`200 OK`)

```json
{
  "chief_complaints": [
    "Acute chest pain and cardiovascular distress",
    "Respiratory distress and shortness of breath",
    "Recorded diagnosis: Hypertension"
  ],
  "patient_symptoms": [
    "Precordial chest discomfort / angina-like symptoms",
    "Acute dyspnea and respiratory effort"
  ],
  "medical_history_summary": "62-year-old Male presenting for clinical assessment. Reported symptoms include: 'i have had severe chest pain radiating to my left arm and breathlessness for the past two hours.'. Documented clinical history of Hypertension. Current pharmacotherapy: Amlodipine (5mg, 1-0-0). Abnormal diagnostic findings: Fasting Blood Sugar: 280 mg/dL. Geriatric vulnerability factor (Age 62). Documented drug allergies: Penicillin.",
  "icd10_codes": [
    {
      "code": "R07.9",
      "description": "Chest pain, unspecified"
    },
    {
      "code": "R06.02",
      "description": "Shortness of breath"
    }
  ],
  "risk_assessment": {
    "risk_level": "Critical",
    "score": 9,
    "red_flags": [
      "Chest pain with potential cardiac involvement",
      "Acute respiratory compromise or dyspnea",
      "Severe Hyperglycemia detected (Fasting Blood Sugar: 280 mg/dL)"
    ],
    "recommended_specialty": "Cardiology"
  },
  "patient_friendly_instructions": "Your symptoms have been flagged for priority attention by our medical team. Please proceed immediately to the Cardiology triage station or alert the nearest nurse. Avoid exerting yourself, sit down in the priority waiting area, and keep your phone accessible. Staff have been notified of your arrival.",
  "provider_used": "mock_offline",
  "processing_time_ms": 1.45
}
```

---

## 5. Mobile App UI Component Mapping Guide

Use this mapping table to bind the backend JSON response fields directly to your mobile app screens:

| JSON Response Field | Type | Mobile UI Component | Recommended Styling & Behavior |
|---|---|---|---|
| `risk_assessment.risk_level` | `string` ("Low", "Medium", "High", "Critical") | **Triage Status Badge** | - **Critical**: Flash Red (`#D32F2F`) + Alert Modal<br>- **High**: Orange/Amber (`#F57C00`)<br>- **Medium**: Yellow (`#FBC02D`)<br>- **Low**: Emerald Green (`#388E3C`) |
| `risk_assessment.score` | `number` (1 to 10) | **Severity Gauge / Progress Bar** | Horizontal progress bar `value / 10`. Colors dynamically with `risk_level`. |
| `risk_assessment.red_flags` | `string[]` | **Warning Banner / Alert Box** | Render red warning box with alert triangle icon (`⚠️`) if list is not empty. |
| `risk_assessment.recommended_specialty` | `string` | **Department Routing Card** | Highlights destination clinic (e.g. *Cardiology*, *General Medicine*) and prompts queue token generation. |
| `chief_complaints` | `string[]` | **Complaint Chips / Tags** | Horizontal scrollable chip tags representing primary visit reasons. |
| `patient_symptoms` | `string[]` | **Symptom Checklist** | Compact checklist showing normalized clinical symptoms detected. |
| `medical_history_summary` | `string` | **Clinical Summary Card** | Expandable card containing the synthesized clinical narrative for the doctor. |
| `icd10_codes` | `Array<{code, description}>` | **ICD-10 Diagnostic Badges** | Tappable tags showing diagnostic codes (e.g. `[R07.9] Chest pain`). |
| `patient_friendly_instructions` | `string` | **Patient Guidance Card** | Prominent readable card with optional Text-to-Speech / Read Aloud audio button. |

---

## 6. Frontend Integration Code Samples

### React Native / Expo (Axios)
```typescript
import axios from 'axios';
import { Platform } from 'react-native';

// Use production Render URL or fallback to localhost for offline dev
const BASE_URL = process.env.REACT_APP_API_URL || 'https://team-aces-sih.onrender.com';

export interface ClinicalResponse {
  chief_complaints: string[];
  patient_symptoms: string[];
  medical_history_summary: string;
  icd10_codes: { code: string; description: string }[];
  risk_assessment: {
    risk_level: 'Low' | 'Medium' | 'High' | 'Critical';
    score: number;
    red_flags: string[];
    recommended_specialty: string;
  };
  patient_friendly_instructions: string;
}

export async function processClinicalIntake(
  voiceTranscript?: string,
  ocrData?: any,
  demographics?: any
): Promise<ClinicalResponse> {
  const response = await axios.post<ClinicalResponse>(`${BASE_URL}/api/v1/llm/process`, {
    voice_transcript: voiceTranscript,
    ocr_data: ocrData,
    patient_demographics: demographics,
  });
  return response.data;
}
```

### Flutter (Dart `http` package)
```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

final String baseUrl = Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

Future<Map<String, dynamic>> submitClinicalIntake({
  String? voiceTranscript,
  Map<String, dynamic>? ocrData,
  Map<String, dynamic>? demographics,
}) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/llm/process'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'voice_transcript': voiceTranscript,
      'ocr_data': ocrData,
      'patient_demographics': demographics,
    }),
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to process clinical triage: ${response.body}');
  }
}
```

### Direct cURL Test
```bash
curl -X POST "https://team-aces-sih.onrender.com/api/v1/llm/process" \
     -H "Content-Type: application/json" \
     -d '{"voice_transcript": "Severe radiating chest pain and breathlessness"}'
```

---

## 7. Automated Test Suite Execution

To verify the engine:
```bash
python -m unittest discover -s module_llm_engine/tests -p "test_*.py" -v
```

Verification covers:
- Combined voice + OCR processing
- Partial inputs (voice only, OCR only)
- Zero-API-Key offline mock mode
- Multi-tier fallback (Gemini -> OpenAI -> Mock)
- Allergy contraindication alerts & red flag escalation
- FastAPI endpoint responses and CORS compliance
