"""
auth.py — authentication routes for law clinic reviewers.

POST /api/auth/register  — create a new reviewer account (admin/seed only)
POST /api/auth/login     — exchange username+password for JWT
GET  /api/auth/me        — return current reviewer profile (requires token)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.store import get_reviewer_store
from app.models.reviewer import (
    LoginRequest,
    ReviewerCreate,
    ReviewerPublic,
    ReviewerRecord,
    TokenResponse,
)
from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=True)


# ── Shared dependency ─────────────────────────────────────────────────────────

def get_current_reviewer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> ReviewerRecord:
    """
    FastAPI dependency — validates the Bearer JWT and returns the ReviewerRecord.
    Raises HTTP 401 on missing / invalid / expired token.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    reviewer_id: str = payload.get("sub", "")
    store = get_reviewer_store()
    reviewer = store.get(reviewer_id)
    if reviewer is None or not reviewer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reviewer account not found or deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return reviewer


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=ReviewerPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new law clinic reviewer",
    description=(
        "Creates a reviewer account.  In production this endpoint should be "
        "protected by an admin secret or removed; for the MVP it is open so "
        "the law clinic supervisor can seed student accounts."
    ),
)
def register(body: ReviewerCreate) -> ReviewerPublic:
    store = get_reviewer_store()

    # Enforce unique username
    existing = store.filter(username=body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken.",
        )

    record = ReviewerRecord(
        username=body.username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        email=body.email,
        role=body.role,
    )
    store.put(record)
    return ReviewerPublic(**record.model_dump())


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain a JWT access token",
)
def login(body: LoginRequest) -> TokenResponse:
    store = get_reviewer_store()
    matches = store.filter(username=body.username)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    reviewer = matches[0]
    if not reviewer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your supervisor.",
        )

    if not verify_password(body.password, reviewer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(reviewer.id, reviewer.username, reviewer.role)
    return TokenResponse(
        access_token=token,
        reviewer_id=reviewer.id,
        username=reviewer.username,
        role=reviewer.role,
        expires_in=expires_in,
    )


@router.get(
    "/me",
    response_model=ReviewerPublic,
    summary="Get current reviewer profile",
)
def me(reviewer: ReviewerRecord = Depends(get_current_reviewer)) -> ReviewerPublic:
    return ReviewerPublic(**reviewer.model_dump())
