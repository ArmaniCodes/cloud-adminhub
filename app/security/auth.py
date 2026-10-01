from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from app.security.token import decode_access_token
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.user_service import get_user_by_id
from app.schemas.user import User

security = HTTPBearer()

# Creates a user-based dependency that checks the decoded token
# and verifies that the user exists in the database.
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

# Creates a role-based dependency that remembers the allowed roles
# and checks the authenticated user's role when a request is made.
def require_role(*roles):
    
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role in roles:
            return current_user
        
        raise HTTPException(
                status_code =403, 
                detail="Forbidden"
        )
        

    return role_checker