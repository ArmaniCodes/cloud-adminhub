from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import LoginUser, LoginResponse,RefreshTokenRequest
from app.database import get_db
from app.services.auth_service import authenticate_user as service_authenticate, refresh_token as service_refresh_token, revoke_refresh_token
router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
def login_user(login: LoginUser, db: Session = Depends(get_db)):
    response = service_authenticate(login, db)
    if not response:
        raise HTTPException(status_code=401,detail="Authentication Failed")

    return response


@router.post("/auth/refresh", response_model = LoginResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    response = service_refresh_token(request.refresh_token,db)
    if not response:
        raise HTTPException(status_code=401,detail="Invalid or expired refresh token" )
    return response

@router.post("/auth/logout",response_model = bool)
def log_out(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    if not revoke_refresh_token(request.refresh_token,db):
        raise HTTPException(status_code=401,detail="Invalid or expired refresh token" )
    return True
