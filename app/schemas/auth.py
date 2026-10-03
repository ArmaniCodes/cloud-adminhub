from pydantic import BaseModel, EmailStr


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginUser(BaseModel):
      email: EmailStr
      password: str

class LoginResponse(BaseModel):
      access_token: str
      token_type: str
      refresh_token: str   
