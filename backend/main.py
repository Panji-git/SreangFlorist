"""
Main FastAPI Application Entry Point for Sreang Florist.
Bespoke Botanical Atelier & Retail Analytics System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Sreang Florist API",
    description="REST API for Sreang Florist E-Catalog & Retail Analytics System (Tugas Akhir)",
    version="1.0.0",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health check endpoint
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "service": "Sreang Florist API",
        "version": "1.0.0",
        "database": "SQLite (sreang_florist.db)",
    }

# Mount static frontend files if directory exists
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
