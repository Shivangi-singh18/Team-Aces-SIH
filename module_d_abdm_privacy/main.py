"""Module D: ABDM & Privacy Standalone FastAPI Microservice.

Provides REST endpoints for ABDM/ABHA OTP login, consent lifecycle,
HL7 FHIR R4 Bundle exports, and DPDP-compliant ephemeral session purging.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router
from .session_manager import session_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("medikiosk.module_d")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown logging."""
    logger.info("Initializing Module D: ABDM & Privacy Microservice (SIH26047)...")
    logger.info(
        "Storage backend active: %s (TTL: %ds)",
        "Redis" if session_manager.is_using_redis else "In-Memory Fallback",
        session_manager.default_ttl,
    )
    logger.info("DPDP Act 2023 zero-retention ephemeral guarantee: ACTIVE")
    yield
    logger.info("Shutting down Module D: ABDM & Privacy Microservice.")


app = FastAPI(
    title="MediKiosk Module D: ABDM & Privacy Microservice",
    description=(
        "Production-ready backend for Ayushman Bharat Digital Mission (ABDM) integration, "
        "ABHA authentication, Consent Artefact generation, HL7 FHIR R4 document bundle conversion, "
        "and DPDP Act 2023 compliant ephemeral session management."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Permissive CORS middleware for Kiosk frontend and mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount core APIRouter
app.include_router(router)


@app.get("/", tags=["System"])
async def root() -> Dict[str, Any]:
    """Root metadata probe."""
    return {
        "service": "MediKiosk Module D: ABDM & Privacy Microservice",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "compliance": ["NHA ABDM Sandbox M1/M2/M3", "DPDP Act 2023", "HL7 FHIR R4"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "module_d_abdm_privacy.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )

