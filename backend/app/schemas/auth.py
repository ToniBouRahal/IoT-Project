from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
