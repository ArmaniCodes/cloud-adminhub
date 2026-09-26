from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from random import randint
from fastapi import HTTPException
from typing import Optional
from enum import Enum

router = APIRouter()

# Enum for role validation
class UserRole(Enum):
    admin = "admin"
    support = "support"
    viewer = "viewer"

class User(BaseModel):
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
def get_users():
    return user_list



# Return 404 if ID not present in user_list else return user
@router.get("/users/{user_id}",response_model=User)
def get_user_by_id(user_id: int):
    user = find_user(user_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")

# Update info about user 
@router.patch("/users/{user_id}", response_model = User)
def update_user(user_id: int, user: UpdateUser):
    _user = find_user(user_id)
    
    if not _user:
        raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")

    # Convert UpdateUser to dictionary but only include what we want to update
    _user.update(user.model_dump(exclude_unset=True))
    return _user

@router.delete("/users/{user_id}",response_model = User)
def delete_user(user_id: int):
    user = find_user(user_id)
    if not user:
            raise HTTPException(status_code=404, detail= f"User with id: {user_id} does not exist")
    user_list.remove(user)
    return user

# Create a new User Endpoint
@router.post("/users",response_model=User)
def post_user(user: CreateUser):
    # Generate random temp id for now
    generate_id = randint(1,1000)
    new_user = {'id':generate_id}
    new_user.update(user.model_dump())
    user_list.append(new_user)
    return new_user