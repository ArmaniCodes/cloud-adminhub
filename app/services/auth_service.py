from datetime import datetime, timedelta, timezone
from app.security.token import create_access_token, create_refresh_token, hash_refresh_token
from app.security.password import verify_password
from app.schemas.auth import LoginUser, LoginResponse
from app.models.refresh_token import RefreshToken
from app.models.user import User as UserModel
from sqlalchemy.orm import Session
from app.services.user_service import get_user_by_email
from sqlalchemy.exc import IntegrityError

def store_refresh_token(user: UserModel, refresh_token_hash: str, db: Session):
    refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = refresh_token_hash,
        expires_at = datetime.now(timezone.utc) + timedelta(days=7),
        revoked = False
    )

    db.add(refresh_token)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise


def authenticate_user(login: LoginUser, db: Session):
    # Normalize email for database lookup
    user = get_user_by_email( str(login.email).lower(), db)
    if not user:
        return None

    if verify_password(login.password, user.password_hash):
        token = create_access_token(user.id, user.role)
        token_type = "Bearer"
        refresh_token = create_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token)
        store_refresh_token(user,refresh_token_hash,db)
        return LoginResponse(
            access_token = token, 
            token_type = token_type,
            refresh_token = refresh_token
        )

    return None
    