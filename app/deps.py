from typing import Generator

from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

from .db.database import SessionLocal

API_KEYS = {
    "key_tenant_a": "tenant_a",
    "key_tenant_b": "tenant_b",
}


def get_tenant_id(x_api_key: str = Header(default=None, alias="X-API-Key")) -> str:
    """
    Extract tenant_id from the request header.

    - Client sends: X-API-Key: <key>
    - We map that key to a tenant_id (like 'tenant_a')
    - If missing/invalid -> 401 Unauthorized
    """
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return API_KEYS[x_api_key]


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
