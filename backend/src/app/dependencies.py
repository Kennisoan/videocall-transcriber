from fastapi import Header, HTTPException, Cookie
from typing import Optional
from .database import SessionLocal


def verify_token(x_token: Optional[str] = Header(None), authToken: Optional[str] = Cookie(None)):
    from .routers.auth import AUTH_TOKEN
    token = x_token or authToken
    if not token or token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
