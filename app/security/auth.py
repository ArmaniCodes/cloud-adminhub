from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, APIRouter, HTTPException
from app.security.token import decode_access_token
router = APIRouter()

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    decoded_token = decode_access_token(credentials.credentials)
    if not decoded_token:
        raise HTTPException(
            status_code = 401,
            detail = f'Unauthorized'
        )
    return decoded_token

@router.get("/auth/test")
def auth_test(current_user: str= Depends(get_current_user)):
    return current_user