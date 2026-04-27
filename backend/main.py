"""
============================================================
Generative AI Analysis Platform — FastAPI Entry Point
============================================================
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from database.session import engine, Base
from database import models  # noqa: F401 — registers models with Base

# ── Create tables before anything else ────────────────────
Base.metadata.create_all(bind=engine)

# ── Import routers (restore runs at import time in datasets.py) ──
from api.datasets import router as datasets_router
from api.queries import router as queries_router
from api.voice import router as voice_router
from api.multi_query import router as multi_query_router
from auth.router import router as auth_router
from api.saved_queries import router as saved_queries_router
from api.alerts import router as alerts_router
from api.reports import router as reports_router
from api.compare import router as compare_router
from api.chat import router as chat_router
from api.scenario import router as scenario_router


# ── Lifespan: runs on startup and shutdown ─────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — restore datasets from Neon into memory
    from api.datasets import restore_datasets_from_db
    restore_datasets_from_db()
    yield
    # Shutdown (nothing needed)


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title="Generative AI Analysis Platform",
    description="Natural-language data analysis for non-technical business users",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────
_allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "https://aether-frontend-f0tf.onrender.com",
]
# Remove empty strings and duplicates
_allowed_origins = list(set(o for o in _allowed_origins if o))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Routers ─────────────────────────────────────────
app.include_router(auth_router,           prefix="/api/auth",           tags=["Authentication"])
app.include_router(datasets_router,       prefix="/api/datasets",       tags=["Datasets"])
app.include_router(queries_router,        prefix="/api/queries",        tags=["Queries"])
app.include_router(voice_router,          prefix="/api/voice",          tags=["Voice"])
app.include_router(multi_query_router,    prefix="/api/multi-query",    tags=["Multi-Dataset Query"])
app.include_router(saved_queries_router,  prefix="/api/saved-queries",  tags=["Saved Queries"])
app.include_router(alerts_router,         prefix="/api/alerts",         tags=["Smart Alerts"])
app.include_router(reports_router,        prefix="/api/reports",        tags=["Reports"])
app.include_router(compare_router,        prefix="/api/compare",        tags=["Compare"])
app.include_router(chat_router,           prefix="/api/chat",           tags=["Chat"])
app.include_router(scenario_router,       prefix="/api/scenario",       tags=["Scenario"])


@app.get("/health", tags=["Root"])
@app.get("/", tags=["Root"])
def root():
    """
    Health-check endpoint.
    Returns live status of LLM engine and database dialect.
    """
    from llm.llm_engine import llm_engine
    from database.session import _is_sqlite

    return {
        "status":    "ok",
        "message":   "Generative AI Analysis Platform is running",
        "llm_mode":  "stub" if llm_engine.is_stub else "gemini",
        "llm_model": getattr(llm_engine, "model_name", None),
        "db_mode":   "sqlite" if _is_sqlite else "postgresql",
    }
