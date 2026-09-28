from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from random import randint
from fastapi import HTTPException
from typing import Optional
from enum import Enum
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User as UserModel
from sqlalchemy import select

router = APIRouter()

# Enum for role validation
class UserRole(Enum):
    admin = "admin"
    support = "support"
    viewer = "viewer"

class User(BaseModel):
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


# In-memory test users for development purposes
user_list = [{'id': 23,'name':"John Smith",'email':'john@doe.com',"role":"admin"},
             {'id': 12,'name':"Sarah Smith",'email':'jane@doe.com',"role":"support"}
             ]

# Search for user by ID then return user
def find_user(user_id: int) -> Optional[dict]:
    for d in user_list:
        if d.get('id') == user_id:
            return d


# Users endpoint
@router.get("/users",response_model=list[User])
def get_users(db: Session = Depends(get_db)):
    stmt = select(UserModel)
    users = db.scalars(stmt).all()
    return users



# Return 404 if ID not present in the db
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

    # Set role to str type not enum type so its compatible with the DB
    user_input = user_update.model_dump(exclude_unset=True)
    if "role" in user_input and type(user_input["role"]) == UserRole:
         user_input["role"] = user_input["role"].value
    
    for k,v in user_input.items():
        setattr(user,k,v)   

    db.commit()
    db.refresh(user)
    return user
   

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int):
    user = find_user(user_id)
    if not user:
            raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")
    user_list.remove(user)
    return user

# Create a new User Endpoint
@router.post("/users",response_model=User)
def post_user(user: CreateUser, db: Session = Depends(get_db)):
    userm = UserModel(
        name = user.name,
        email = user.email,
        role = user.role.value
    )
    db.add(userm)
    db.commit()
    db.refresh(userm)
    return userm