from pydantic import BaseModel, EmailStr
from app.schemas.password import NewPassword

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginUser(BaseModel):
      email: EmailStr
      password: str

class LoginResponse(BaseModel):
      access_token: str
      token_type: str
      refresh_token: str   

class ChangePasswordRequest(BaseModel):
     current_password: str
     new_password: NewPassword