from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import LoginUser, User
from app.database import get_db
from app.services.user_service import authenticate_user as service_authenticate
router = APIRouter()

@router.post("/auth/login", response_model=User)
def login_user(login: LoginUser, db: Session = Depends(get_db)):
    user = service_authenticate(login,db)
    if not user:
        raise HTTPException(401,f'Authentication Failed')
    return user