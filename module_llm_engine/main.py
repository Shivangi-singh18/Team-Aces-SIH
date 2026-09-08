"""MediKiosk LLM Orchestration Engine - Mobile-Ready FastAPI Microservice.

Provides high-throughput REST APIs for the MediKiosk Mobile Application,
Android/iOS emulators, and Kiosk Terminals with zero-friction CORS.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import config
from .llm_processor import engine
from .schemas import ClinicalLLMResponse, LLMProcessingRequest

logger = logging.getLogger("medikiosk.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown logging."""
    logger.info("Starting MediKiosk LLM Orchestration Engine (SIH26047)...")
    logger.info("Preferred active provider: %s", config.get_preferred_provider())
    logger.info("CORS policy: allow_origins=['*'] enabled for mobile emulators.")
    yield
    logger.info("Shutting down MediKiosk LLM Orchestration Engine.")


app = FastAPI(
    title="MediKiosk LLM Orchestration Engine",
    description=(
        "Clinical intelligence backend for Project MediKiosk (SIH26047). "
        "Synthesizes patient voice transcripts, digitized OCR prescriptions/labs, "
        "and demographics into clinical triage summaries with ICD-10 coding and risk stratification."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure permissive CORS middleware for mobile emulators & web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Kubernetes, Docker, and Mobile App connectivity probes."""
    return {
        "status": "healthy",
        "service": "MediKiosk LLM Orchestration Engine",
        "version": "1.0.0",
        "active_provider": config.get_preferred_provider(),
        "mock_mode_active": config.FORCE_MOCK_MODE or not (config.is_gemini_configured() or config.is_openai_configured()),
    }


@app.get("/api/v1/llm/providers", tags=["Intelligence"])
async def get_providers_status() -> Dict[str, Any]:
    """Inspect availability of AI inference providers."""
    return {
        "preferred_provider": config.get_preferred_provider(),
        "providers": {
            "gemini": {
                "configured": config.is_gemini_configured(),
                "model": config.GEMINI_MODEL,
            },
            "openai": {
                "configured": config.is_openai_configured(),
                "model": config.OPENAI_MODEL,
            },
            "mock_offline": {
                "configured": True,
                "forced": config.FORCE_MOCK_MODE,
                "description": "Deterministic rule-based clinical triage engine (Zero API Key required)",
            },
        },
    }


@app.post(
    "/api/v1/llm/process",
    response_model=ClinicalLLMResponse,
    status_code=status.HTTP_200_OK,
    tags=["Intelligence"],
    summary="Process multi-modal patient inputs into clinical triage assessment",
)
async def process_clinical_intake(request: LLMProcessingRequest) -> ClinicalLLMResponse:
    """Core intelligence endpoint.

    Takes patient voice transcripts, OCR digitized documents (Module B contract),
    and demographics to return structured clinical triage, ICD-10 codes, risk scores,
    and patient-friendly guidance.
    """
    try:
        response = await engine.aprocess(request)
        return response
    except Exception as exc:
        logger.error("Error processing clinical intake: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clinical engine processing failure: {str(exc)}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "module_llm_engine.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    )
