from fastapi import HTTPException
from app.core.errors import (
    NotFoundError,
    ConflictError,
    BadRequestError,
    RateLimitError,
)


def raise_http(e: Exception) -> None:
    if isinstance(e, NotFoundError):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, ConflictError):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, BadRequestError):
        raise HTTPException(status_code=400, detail=str(e))
    if isinstance(e, RateLimitError):
        raise HTTPException(status_code=429, detail=str(e))
    raise HTTPException(status_code=500, detail="Internal server error")
