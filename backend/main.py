"""
============================================================
Generative AI Analysis Platform — FastAPI Entry Point
============================================================
This is the main application file. It:
  1. Creates the FastAPI app instance
  2. Configures CORS middleware
  3. Mounts all API routers
  4. Creates database tables on startup
============================================================
"""

import os
from dotenv import load_dotenv

# Load .env into OS environment FIRST — before any module calls os.getenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database.session import engine, Base
from api.datasets import router as datasets_router
from api.queries import router as queries_router
from api.voice import router as voice_router
from auth.router import router as auth_router

# ── Create database tables on import ──────────────────────
# In production, use Alembic migrations instead.
from database import models  # noqa: F401 — registers models with Base
Base.metadata.create_all(bind=engine)

# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title="Generative AI Analysis Platform",
    description="Natural-language data analysis for non-technical business users",
    version="1.0.0",
)

# ── CORS Middleware ───────────────────────────────────────
# Allows the React frontend to communicate with the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Routers ─────────────────────────────────────────
app.include_router(auth_router,     prefix="/api/auth",     tags=["Authentication"])
app.include_router(datasets_router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(queries_router,  prefix="/api/queries",  tags=["Queries"])
app.include_router(voice_router,    prefix="/api/voice",    tags=["Voice"])


@app.get("/", tags=["Root"])
def root():
    """Health-check endpoint."""
    return {"status": "ok", "message": "Generative AI Analysis Platform is running"}
