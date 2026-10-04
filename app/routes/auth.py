from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import LoginUser, LoginResponse,RefreshTokenRequest,ChangePasswordRequest
from app.models.user import User as UserModel
from app.schemas.user import User
from app.database import get_db
from app.security.auth import get_current_user
from app.services.auth_service import (authenticate_user as service_authenticate,
        refresh_token as service_refresh_token,
          revoke_refresh_token, change_password as service_change_password
          )
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

@router.post("/auth/logout", status_code = status.HTTP_204_NO_CONTENT)
def log_out(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    if not revoke_refresh_token(request.refresh_token,db):
        raise HTTPException(status_code=401,detail="Invalid or expired refresh token" )
    return True

@router.get("/auth/me", response_model=User)
def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.post("/auth/change-password", status_code = status.HTTP_204_NO_CONTENT)
def change_password(
    password_details: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db) 
):
    
    if not service_change_password(password_details,current_user,db):
        raise HTTPException(status_code=403,detail="Incorrect current password" )
   
