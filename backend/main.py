"""
FormFlow Backend — FastAPI Application
========================================
Entry point. Registers all routes, middleware, CORS, and startup checks.

Run with:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
import logging
import os
import sys

from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.schema import HealthResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FormFlow API",
    description="Transform complicated forms into guided applications.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
additional_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
if frontend_url not in additional_origins:
    additional_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=additional_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ---------------------------------------------------------------------------
# Global exception handler (never expose raw tracebacks to users)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred.",
            "detail": "The server encountered an error. Please try again.",
            "code": "INTERNAL_ERROR",
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
from routes.analyze import router as analyze_router
from routes.validate import router as validate_router
from routes.export import router as export_router
from routes.documents import router as documents_router

app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(validate_router, prefix="/api", tags=["Validation"])
app.include_router(export_router, prefix="/api", tags=["Export"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Returns server status and AI configuration."""
    from services.ai_provider import create_ai_provider
    provider, mode = create_ai_provider()
    return HealthResponse(
        status="ok",
        ai_configured=(mode == "real"),
        ai_provider=provider.name,
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "FormFlow API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("FormFlow API starting...")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key and api_key not in ("", "your-api-key-here"):
        logger.info("✓ Gemini API key configured — real AI mode available")
    else:
        logger.warning(
            "⚠ No Gemini API key configured — running in Demo Mode only. "
            "Set GEMINI_API_KEY in .env to enable real document analysis."
        )

    logger.info("✓ FormFlow API ready")
    logger.info("=" * 60)
