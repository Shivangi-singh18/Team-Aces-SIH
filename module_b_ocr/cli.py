"""Command-Line Interface for Module B Medical Document OCR & Digitization Pipeline.

Usage examples:
    # Run on an existing prescription image
    python -m module_b_ocr.cli path/to/prescription.jpg

    # Run on a lab report with printed engine and gemini provider
    python -m module_b_ocr.cli path/to/report.png --engine printed --provider gemini --output result.json

    # Test pipeline with built-in synthetic OPD prescription
    python -m module_b_ocr.cli --mock-sample prescription

    # Test pipeline with built-in synthetic pathology report
    python -m module_b_ocr.cli --mock-sample lab_report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .entity_extractor import extract_clinical_entities
from .pipeline import process_medical_document_full
from .schemas import MedicalDocumentSchema


def create_synthetic_sample_image(sample_type: str = "prescription") -> Image.Image:
    """Generate a clean synthetic medical document image for testing without external files."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    if sample_type == "prescription":
        lines = [
            "CITY MULTISPECIALITY CLINIC & OPD",
            "Dr. R. K. Sharma, MD (Medicine)",
            "Reg No: DMC/19842/2012  |  Date: 08-Sep-2026",
            "--------------------------------------------------",
            "Patient: Rajesh Kumar, Age: 45 Y / Male",
            "C/o: High grade fever with chills, body ache x 3 days",
            "Dx: Upper Respiratory Tract Infection, Viral Fever",
            "--------------------------------------------------",
            "Rx:",
            "1. Tab. Paracetamol 650mg - 1-0-1 - 5 days",
            "2. Tab. Augmentin 625mg - 1-0-1 - 5 days",
            "3. Tab. Pantop 40mg - 1-0-0 (Before food) - 5 days",
            "4. Tab. Montair-LC - 0-0-1 - 7 days",
            "--------------------------------------------------",
            "Advice: Steam inhalation twice daily, drink warm water.",
            "Review in OPD after 5 days if fever persists.",
        ]
    else:
        lines = [
            "METROPOLIS PATHOLOGY & DIAGNOSTIC CENTER",
            "NABL ACCREDITED LABORATORY",
            "Patient: Sunita Devi, Age: 52 Y / Female",
            "Ref Doctor: Dr. A. Gupta  |  Sample: Serum & Whole Blood",
            "==================================================",
            "TEST NAME                  VALUE    UNIT      REF RANGE",
            "==================================================",
            "Hemoglobin                 9.8      g/dL      12.0 - 15.5  (Low)",
            "Fasting Blood Sugar        158.0    mg/dL     70 - 100     (High)",
            "Post Prandial Blood Sugar  210.0    mg/dL     < 140        (High)",
            "HbA1c                      8.4      %         < 5.7        (High)",
            "Serum Creatinine           1.1      mg/dL     0.6 - 1.2    Normal",
            "Blood Urea                 32.0     mg/dL     15 - 45      Normal",
            "Total Leukocyte Count      12500    /cumm     4000 - 11000 (High)",
            "Platelet Count             2.4      lakhs/cumm 1.5 - 4.5   Normal",
            "==================================================",
            "End of Laboratory Investigation Report",
        ]

    y = 30
    for line in lines:
        draw.text((30, y), line, fill=(20, 20, 20))
        y += 35

    return img


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Module B (MediKiosk) - Medical Document OCR & Entity Digitization Pipeline",
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        type=str,
        help="Path to medical document image (JPEG, PNG, etc.).",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="auto",
        choices=["auto", "printed", "handwritten", "gcv", "azure", "trocr", "easyocr"],
        help="OCR engine selection (default: auto).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        choices=["auto", "gemini", "openai", "heuristic"],
        help="Entity extraction provider (default: auto).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output JSON file path (prints to stdout if omitted).",
    )
    parser.add_argument(
        "--mock-sample",
        type=str,
        choices=["prescription", "lab_report"],
        help="Run on an auto-generated sample image for demonstration.",
    )

    args = parser.parse_args()

    if args.mock_sample:
        print(f"Generating synthetic test medical {args.mock_sample}...")
        img = create_synthetic_sample_image(args.mock_sample)
        # If running mock sample without active cloud OCR, parse the synthetic text directly through clinical extractor
        if args.mock_sample == "prescription":
            raw_sample_text = (
                "CITY MULTISPECIALITY CLINIC & OPD\n"
                "Dr. R. K. Sharma, MD (Medicine)\n"
                "Patient: Rajesh Kumar, Age: 45 Y / Male\n"
                "Dx: Upper Respiratory Tract Infection, Viral Fever\n"
                "Rx:\n"
                "1. Tab. Paracetamol 650mg - 1-0-1 - 5 days\n"
                "2. Tab. Augmentin 625mg - 1-0-1 - 5 days\n"
                "3. Tab. Pantop 40mg - 1-0-0 - 5 days\n"
                "4. Tab. Montair-LC - 0-0-1 - 7 days\n"
            )
        else:
            raw_sample_text = (
                "METROPOLIS PATHOLOGY & DIAGNOSTIC CENTER\n"
                "Patient: Sunita Devi, Age: 52 Y / Female\n"
                "Hemoglobin: 9.8 g/dL (Low)\n"
                "Fasting Blood Sugar: 158.0 mg/dL (High)\n"
                "Post Prandial Blood Sugar: 210.0 mg/dL (High)\n"
                "HbA1c: 8.4 % (High)\n"
                "Serum Creatinine: 1.1 mg/dL\n"
                "Blood Urea: 32.0 mg/dL\n"
                "Total Leukocyte Count: 12500 /cumm (High)\n"
                "Platelet Count: 2.4 lakhs/cumm\n"
            )

        entities = extract_clinical_entities(raw_sample_text, provider=args.provider)
        result_json = entities.to_json(indent=2)
        print("\n=== Extracted Structured JSON Payload ===")
        print(result_json)
        if args.output:
            Path(args.output).write_text(result_json, encoding="utf-8")
            print(f"\nSaved structured output to: {args.output}")
        return

    if not args.image_path:
        parser.print_help()
        sys.exit(1)

    image_path = Path(args.image_path)
    if not image_path.exists():
        print(f"Error: Input file does not exist: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing image: {image_path}...")
    res = process_medical_document_full(
        image_input=image_path,
        ocr_engine=args.engine,
        llm_provider=args.provider,
    )

    output_str = res.to_json(indent=2)
    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"Digitization complete! Output saved to: {args.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
