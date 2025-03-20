from fastapi import Header, HTTPException, Cookie, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from .database import SessionLocal
from .auth import get_current_active_user
from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency that requires authentication
def get_current_user_dependency(current_user=Depends(get_current_active_user)):
    return current_user
