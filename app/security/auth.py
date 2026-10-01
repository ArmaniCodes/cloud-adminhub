from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, APIRouter, HTTPException
from app.security.token import decode_access_token
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.user_service import get_user_by_id
from app.schemas.user import User

router = APIRouter()

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    decoded_token = decode_access_token(credentials.credentials)
    if not decoded_token:
        raise HTTPException(
            status_code = 401,
            detail = "Unauthorized"
        )

    user = get_user_by_id(decoded_token["id"], db)
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail= "Unauthorized"
        )
    
    return user

@router.get("/auth/test", response_model=User)
def auth_test(current_user: User = Depends(get_current_user)):
    return current_user