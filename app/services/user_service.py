from sqlalchemy.orm import Session
from app.schemas.user import CreateUser, UpdateUser, UserRole
from app.models.user import User as UserModel
from sqlalchemy import select
from app.exceptions.user import UserAlreadyExistsError
from sqlalchemy.exc import IntegrityError
from app.security.password import hash_password
from app.database import transaction

def create_user(user: CreateUser, db: Session):
    userm = UserModel(
            name = user.name,
            email = str(user.email).lower(),
            role = user.role.value,
            password_hash = hash_password(user.password)
        )
    try:
        with transaction(db):
            db.add(userm)
    except IntegrityError:
        raise UserAlreadyExistsError()
    
    db.refresh(userm)
    return userm

def get_user_by_id(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    return user

def normalize_user(user_input: dict) -> None:
    # Normalize email
    if "email" in user_input:
        user_input["email"] = str(user_input["email"]).lower()
    if "role" in user_input and isinstance(user_input["role"], UserRole):
        user_input["role"] = user_input["role"].value

def update_user(user_id: int, updated_info: UpdateUser, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    
    user_input = updated_info.model_dump(exclude_unset=True)
    normalize_user(user_input)

    try:
        with transaction(db):
            for k,v in user_input.items():
                setattr(user,k,v)
    except IntegrityError:
        raise UserAlreadyExistsError()

    db.refresh(user)
    return user 

def delete_user(user_id: int, db: Session):
    user = db.get(UserModel,user_id)
    if not user:
        return None
    with transaction(db):
        db.delete(user)
    return user

def list_users(db: Session):
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users

def get_user_by_email(user_email: str, db: Session):
    stmt = select(UserModel).filter_by(email=user_email)
    user = db.scalar(stmt)
    return user

