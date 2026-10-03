from datetime import datetime, timedelta, timezone
from app.security.token import create_access_token, create_refresh_token, hash_refresh_token
from app.security.password import verify_password
from app.schemas.auth import LoginUser, LoginResponse
from app.models.refresh_token import RefreshToken
from app.models.user import User as UserModel
from sqlalchemy.orm import Session
from app.services.user_service import get_user_by_email, get_user_by_id
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

def build_refresh_token(user: UserModel, refresh_token_hash: str):
    refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = refresh_token_hash,
        expires_at = datetime.now(timezone.utc) + timedelta(days=7),
        revoked = False
    )

    return refresh_token

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
        refresh_token_orm = build_refresh_token(user,refresh_token_hash)
        db.add(refresh_token_orm)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise

        return LoginResponse(
            access_token = token, 
            token_type = token_type,
            refresh_token = refresh_token
        )

    return None


def get_refresh_token(refresh_token: str, db: Session):
    token_hash = hash_refresh_token(refresh_token)
    stmt = select(RefreshToken).filter_by(token_hash = token_hash)
    refresh_token_orm = db.scalar(stmt)
    return refresh_token_orm

def validate_refresh_token(refresh_token: str, db: Session):
    refresh_token_orm = get_refresh_token(refresh_token,db)
    if (not refresh_token_orm
        or refresh_token_orm.revoked
        or refresh_token_orm.expires_at <= datetime.now(timezone.utc)
    ):
        return None
    
    return refresh_token_orm

def get_user_by_refresh_token(refresh_token_orm: RefreshToken, db: Session):
    if not refresh_token_orm:
        return None
    user_id = refresh_token_orm.user_id
    user = get_user_by_id(user_id, db)
    return user

def refresh_token(refresh_token: str, db: Session):
    refresh_token_orm = validate_refresh_token(refresh_token,db)
    user = get_user_by_refresh_token(refresh_token_orm, db)

    if not refresh_token_orm or not user:
        return None
    
    refresh_token_orm.revoked = True
    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token()
    new_hashed_token = hash_refresh_token(new_refresh_token)
    new_refresh_token_orm = build_refresh_token(user,new_hashed_token)
    
    db.add(new_refresh_token_orm)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    return LoginResponse(
        access_token = access_token, 
        token_type = "Bearer",
        refresh_token = new_refresh_token
    )

def revoke_refresh_token(refresh_token: str, db: Session):
    refresh_token_orm = validate_refresh_token(refresh_token, db)
    if not refresh_token_orm:
        return False
    refresh_token_orm.revoked = True
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    return True
    