from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$",
        description="3-32 chars: letters, digits, underscore only.",
    )
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: int
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
