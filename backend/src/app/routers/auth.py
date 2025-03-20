from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
import os

from ..database import get_db
from ..schemas import Token, UserCreate, User, LoginRequest
from ..crud import create_user, get_user_by_username
from ..auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["auth"])

# Legacy authentication - will be deprecated
GLOBAL_PASSWORD = os.environ.get("APP_GLOBAL_PASSWORD", "supersecret")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "myauthtoken")


# Legacy login endpoint - will be deprecated once all clients are updated
@router.post("/login")
def login(credentials: LoginRequest):
    if credentials.password == GLOBAL_PASSWORD:
        response = JSONResponse({"token": AUTH_TOKEN})
        response.set_cookie(key="authToken", value=AUTH_TOKEN, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Incorrect password")


# New authentication endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = JSONResponse(
        {"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(key="authToken", value=access_token, httponly=True)
    return response


@router.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)
