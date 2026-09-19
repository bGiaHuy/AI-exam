"""
================================================================================
FASTAPI ROOT APPLICATION - AI EXAM CONTROL
================================================================================
Minimal Scope Vision Proctoring Server:
  - Database: SQLite (cheating_system.db) with WAL mode
  - Routers: incidents, settings, ai_engine, camera
  - Static Mount: ./data/evidence mounted at /evidence
  - CORS: http://localhost:3000, http://localhost:5173
  - Zero identity handling.
================================================================================
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add backend directory to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# Ensure models and database are registered
from database import engine, Base
from routers import incidents, settings, ai_engine

# Ensure SQLite tables exist
Base.metadata.create_all(bind=engine)

# Ensure static evidence directory exists
BASE_DIR = os.path.dirname(CURRENT_DIR)
EVIDENCE_DIR = os.path.join(BASE_DIR, "data", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

# Initialize FastAPI App
app = FastAPI(
    title="AI Exam Control - Vision Proctoring Engine",
    description="Real-time exam violation surveillance with automated video evidence extraction (Offline On-Premise)",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Evidence Directory
app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")

# Register Minimal Routers with prefix /api
app.include_router(incidents.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(ai_engine.router, prefix="/api")

# Guarded Test Endpoints: Default is False in production. Only mount when explicit flag or test environment
ENABLE_TEST_ENDPOINTS = os.getenv("ENABLE_TEST_ENDPOINTS", "false").lower() in ("true", "1", "yes") or os.getenv("ENVIRONMENT", "").lower() == "test"
if ENABLE_TEST_ENDPOINTS:
    app.include_router(ai_engine.test_router, prefix="/api")

# Guarded Deprecated Ingest: Default is False. Base64 frame ingest disabled to prevent parallel pipeline leakage
ENABLE_DEPRECATED_INGEST = os.getenv("ENABLE_DEPRECATED_INGEST", "false").lower() in ("true", "1", "yes")
if ENABLE_DEPRECATED_INGEST:
    app.include_router(ai_engine.deprecated_router, prefix="/api")

# Guarded Legacy Clips Route: Default is False. Canonical route is /evidence/{filename}
ENABLE_LEGACY_CLIPS = os.getenv("ENABLE_LEGACY_CLIPS", "false").lower() in ("true", "1", "yes")
if ENABLE_LEGACY_CLIPS:
    app.include_router(ai_engine.legacy_clips_router, prefix="/api")



@app.get("/api/health")
def health_check():
    """
    Health check endpoint for system monitoring.
    """
    return {
        "status": "ONLINE",
        "mode": "OFFLINE_LOCAL",
        "database": "SQLite 3 (WAL)",
        "evidence_storage": EVIDENCE_DIR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
