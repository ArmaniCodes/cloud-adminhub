from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from fastapi import HTTPException
from typing import Optional
from enum import Enum
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User as UserModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

# Allowed roles for users
class UserRole(Enum):
    admin = "admin"
    support = "support"
    viewer = "viewer"

class User(BaseModel):
        # Allow Pydantic to serialize SQLAlchemy ORM objects
        model_config = ConfigDict(from_attributes=True)
        id: int
        name: str
        email:EmailStr
        role: UserRole

class CreateUser(BaseModel):
     name: str
     email: EmailStr
     role: UserRole

class UpdateUser(BaseModel):
     name: Optional[str] = None
     email: Optional[EmailStr] = None
     role: Optional[UserRole] = None


@router.get("/users",response_model=list[User])
def get_users(db: Session = Depends(get_db)):
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users


@router.get("/users/{user_id}",response_model=User)
def get_user_by_id(user_id: int,  db: Session = Depends(get_db)):
    user = db.get(UserModel,user_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")

# Update info about user 
@router.patch("/users/{user_id}", response_model = User)
def update_user(user_id: int, user_update: UpdateUser, db: Session = Depends(get_db)):
    user = db.get(UserModel,user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")

    # Convert the enum to a string before storing it in the database
    user_input = user_update.model_dump(exclude_unset=True)
    if "role" in user_input and type(user_input["role"]) == UserRole:
         user_input["role"] = user_input["role"].value
    
    for k,v in user_input.items():
        setattr(user,k,v)   

    db.commit()
    db.refresh(user)
    return user
   

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserModel,user_id)
    if not user:
            raise HTTPException(
                 status_code=404, 
                 detail= f"User with id: {user_id} does not exist"
                 )
    
    db.delete(user)
    db.commit()
    return user


@router.post("/users",response_model=User)
def post_user(user: CreateUser, db: Session = Depends(get_db)):
    userm = UserModel(
        name = user.name,
        email = user.email,
        role = user.role.value
    )
    db.add(userm)
    try:
        db.commit()
    except IntegrityError:
         db.rollback()
         raise HTTPException(
            status_code = 409, 
            detail = f'A user with that email already exists.'
        )
    db.refresh(userm)
    return userm