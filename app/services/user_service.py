from sqlalchemy.orm import Session
from app.schemas.user import CreateUser, UpdateUser, UserRole,LoginUser, LoginResponse
from app.models.refresh_token import RefreshToken
from app.models.user import User as UserModel
from sqlalchemy import select
from app.exceptions.user import UserAlreadyExistsError
from sqlalchemy.exc import IntegrityError
from app.security.password import hash_password, verify_password
from app.security.token import create_access_token, create_refresh_token, hash_refresh_token
from datetime import datetime, timedelta, timezone

def create_user(user: CreateUser, db: Session):
    userm = UserModel(
            name = user.name,
            email = str(user.email).lower(),
            role = user.role.value,
            password_hash = hash_password(user.password)
        )
    db.add(userm)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserAlreadyExistsError()
    db.refresh(userm)
    return userm

def get_user_by_id(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    return user

def update_user(user_id: int, updated_info: UpdateUser, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    
    user_input = updated_info.model_dump(exclude_unset=True)

    # Normalize email
    if "email" in user_input:
        user_input["email"] = str(user_input["email"]).lower()
    # Ensure role and password get updated correctly
    if "role" in user_input and isinstance(user_input["role"], UserRole):
        user_input["role"] = user_input["role"].value
    if "password" in user_input:
        user_input["password_hash"] = hash_password(user_input["password"])
        del user_input["password"]

    for k,v in user_input.items():
        setattr(user,k,v)
    
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserAlreadyExistsError()
    
    db.refresh(user)
    return user 

def delete_user(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user

def list_users(db: Session):
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users

def get_user_by_email(user_email: str, db: Session):
    stmt = select(UserModel).filter_by(email=user_email)
    user = db.scalar(stmt)
    return user

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
    