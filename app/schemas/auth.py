from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


# Step 1 - account credentials + optional profile fields
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None


# Step 2 - personal details (all optional so the user can update partially)
class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None
    document_path: Optional[str] = None
    role: str
    is_verified: bool

    model_config = {"from_attributes": True}
