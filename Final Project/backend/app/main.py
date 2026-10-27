"""
main.py — FastAPI application entrypoint for Legal Rights Navigator backend.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import intake, notice, clinic, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure data directories exist and create DB tables
    settings.ensure_dirs()
    from app.db.database import create_db_and_tables
    create_db_and_tables()
    yield
    # Shutdown: nothing needed (SQLite auto-commits; Postgres connection pool managed by engine)


app = FastAPI(
    title="Legal Rights Navigator API",
    description=(
        "Pre-Litigation Engine for SDG 16 LegalTech. "
        "Converts citizen grievances into statute-cited legal notices "
        "verified by law clinic students."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(intake.router)
app.include_router(notice.router)
app.include_router(clinic.router)


@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": (
            settings.ollama_model
            if settings.llm_provider == "ollama"
            else settings.openai_model
        ),
    }
