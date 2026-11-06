import hashlib
import secrets

from fastapi import HTTPException


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_agent_token() -> str:
    return "aura_" + secrets.token_urlsafe(32)


def require_admin(provided: str | None, expected: str) -> None:
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid administrator token")


def extract_bearer(value: str | None) -> str:
    if not value or not value.lower().startswith("bearer ") or not value[7:].strip():
        raise HTTPException(status_code=401, detail="Agent bearer token required")
    return value[7:].strip()
