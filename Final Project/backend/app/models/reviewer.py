"""
reviewer.py — Pydantic models for law clinic reviewer accounts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ReviewerCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, description="Plain-text password — hashed before storage.")
    full_name: str
    email: str
    role: Literal["student", "supervisor"] = "student"


class ReviewerRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    hashed_password: str
    full_name: str
    email: str
    role: Literal["student", "supervisor"] = "student"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Store needs an `id` attribute — already present above.


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    reviewer_id: str
    username: str
    role: str
    expires_in: int  # seconds


class ReviewerPublic(BaseModel):
    """Safe public view — no password hash."""
    id: str
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
