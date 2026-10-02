from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import LoginUser, LoginResponse
from app.database import get_db
from app.services.auth_service import authenticate_user as service_authenticate
router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
def login_user(login: LoginUser, db: Session = Depends(get_db)):
    response = service_authenticate(login, db)
    if not response:
        raise HTTPException(401,f'Authentication Failed')

    return response


