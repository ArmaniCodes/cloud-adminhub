from datetime import datetime, timedelta, timezone
from app.security.token import create_access_token, create_refresh_token, hash_refresh_token
from app.security.password import verify_password, hash_password
from app.schemas.auth import LoginUser, LoginResponse, ChangePasswordRequest
from app.models.refresh_token import RefreshToken
from app.models.user import User as UserModel
from sqlalchemy.orm import Session
from app.services.user_service import get_user_by_email, get_user_by_id
from sqlalchemy import select
from app.database import transaction
from app.services.audit_service import create_audit_log

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
        
        with transaction(db):
            db.add(refresh_token_orm)

        return LoginResponse(
            access_token = token, 
            token_type = token_type,
            refresh_token = refresh_token
        )

    return None

def get_all_unrevoked_user_refresh_tokens(user_id: int, db: Session):
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked.is_(False)
    )
    entries = db.scalars(stmt).all()
    return entries


def get_refresh_token(refresh_token: str, db: Session):
    token_hash = hash_refresh_token(refresh_token)
    stmt = select(RefreshToken).filter_by(token_hash = token_hash)
    refresh_token_orm = db.scalar(stmt)
    return refresh_token_orm

def is_refresh_token_expired(refresh_token_orm: RefreshToken) -> bool:
    return refresh_token_orm.expires_at <= datetime.now(timezone.utc)

def validate_refresh_token(refresh_token: str, db: Session):
    refresh_token_orm = get_refresh_token(refresh_token,db)
    
    if not refresh_token_orm:
        return None

    if refresh_token_orm.revoked:
        entries = get_all_unrevoked_user_refresh_tokens(
            refresh_token_orm.user_id, db
        )
        with transaction(db):
            for entry in entries:
                entry.revoked = True
        return None
        
    if is_refresh_token_expired(refresh_token_orm):
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

    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token()
    new_hashed_token = hash_refresh_token(new_refresh_token)
    new_refresh_token_orm = build_refresh_token(user,new_hashed_token)

    with transaction(db):
        refresh_token_orm.revoked = True
        db.add(new_refresh_token_orm)

    return LoginResponse(
        access_token = access_token, 
        token_type = "Bearer",
        refresh_token = new_refresh_token
    )

def revoke_refresh_token(refresh_token: str, db: Session):
    refresh_token_orm = validate_refresh_token(refresh_token, db)
    if not refresh_token_orm:
        return False
    with transaction(db):
        refresh_token_orm.revoked = True
    return True

def change_password(password_details: ChangePasswordRequest,current_user: UserModel, db: Session) -> bool:
    if verify_password(
        password_details.current_password,
        current_user.password_hash
    ):
         entries = get_all_unrevoked_user_refresh_tokens(current_user.id,db)
         with transaction(db):
            current_user.password_hash = hash_password(password_details.new_password)
            for entry in entries:
                entry.revoked = True
            create_audit_log(current_user.id, "PASSWORD_CHANGED", current_user.id, "Password changed; all active refresh sessions revoked",db)

         return True
    return False
       