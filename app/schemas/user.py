from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from enum import Enum

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
     password: str

class UpdateUser(BaseModel):
     name: Optional[str] = None
     email: Optional[EmailStr] = None
     role: Optional[UserRole] = None
     password: Optional[str] = None

class LoginUser(BaseModel):
      email: EmailStr
      password: str