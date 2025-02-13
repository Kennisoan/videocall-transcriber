from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

router = APIRouter(tags=["auth"])

GLOBAL_PASSWORD = os.environ.get("APP_GLOBAL_PASSWORD", "supersecret")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "myauthtoken")


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(credentials: LoginRequest):
    if credentials.password == GLOBAL_PASSWORD:
        response = JSONResponse({"token": AUTH_TOKEN})
        response.set_cookie(key="authToken", value=AUTH_TOKEN, httponly=True)
        return response
    raise HTTPException(status_code=401, detail="Incorrect password")
