"""
conftest.py — shared pytest fixtures for the backend test suite.

Uses FastAPI's TestClient with a temp-directory data store so tests
are isolated from each other and from any production data files.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# ── Make backend/app importable ───────────────────────────────────────────────
_BACKEND_ROOT = Path(__file__).parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# ── Point the store at a per-test SQLite database ────────────────────────────
@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """
    Each test gets its own temp directory and an isolated SQLite database.
    The engine and stores are reset after each test.
    """
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PDF_DIR", str(tmp_path / "pdfs"))
    (tmp_path / "pdfs").mkdir()

    # Re-create the engine with the new DATABASE_URL
    import app.db.database as db_module
    import app.db.store as store_module
    import app.db.sql_models  # noqa: F401  — registers table metadata before create_all
    from sqlmodel import SQLModel, create_engine

    new_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    db_module.engine = new_engine
    SQLModel.metadata.create_all(new_engine)

    # Reset store singletons
    store_module._case_store = None
    store_module._notice_store = None
    store_module._reviewer_store = None

    yield tmp_path

    # Cleanup
    store_module._case_store = None
    store_module._notice_store = None
    store_module._reviewer_store = None
    new_engine.dispose()


@pytest.fixture()
def client(isolated_data_dir):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


# ── Auth helpers ──────────────────────────────────────────────────────────────

_REVIEWER_USERNAME = "test_student"
_REVIEWER_PASSWORD = "testpassword123"


def register_reviewer(client) -> str:
    """Register a test reviewer and return their JWT token."""
    reg = client.post("/api/auth/register", json={
        "username": _REVIEWER_USERNAME,
        "password": _REVIEWER_PASSWORD,
        "full_name": "Test Student",
        "email": "student@clinic.test",
        "role": "student",
    })
    # 201 on first call, 409 on subsequent calls within same test run
    assert reg.status_code in (201, 409), reg.text

    login = client.post("/api/auth/login", json={
        "username": _REVIEWER_USERNAME,
        "password": _REVIEWER_PASSWORD,
    })
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


@pytest.fixture()
def auth_token(client):
    """Returns a valid Bearer token for the test reviewer."""
    return register_reviewer(client)


@pytest.fixture()
def auth_headers(auth_token):
    """Returns Authorization header dict ready for TestClient."""
    return {"Authorization": f"Bearer {auth_token}"}


# ── A fully-collected set of facts for use in notice/clinic tests ──────────────
FULL_FACTS = {
    "claimant_name": "Priya Sharma",
    "respondent_name": "QuickMart Pvt Ltd",
    "incident_date": "2024-03-15",
    "claim_amount_inr": 25000.0,
    "evidence_summary": "Receipt No. 4521, WhatsApp screenshots, product photos",
    "dispute_category": "consumer_fraud",
}
