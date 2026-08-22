from pydantic import BaseModel, EmailStr, field_validator
from datetime import date
from typing import Optional


def _validate_national_id(v: Optional[str]) -> Optional[str]:
    if v is not None and v.strip():
        cleaned = v.strip()
        if not cleaned.isdigit() or len(cleaned) != 8:
            raise ValueError('National ID must be exactly 8 digits')
        return cleaned
    return v


# Step 1 - account credentials + optional profile fields
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    professional_name: Optional[str] = None
    religious_name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None

    @field_validator('national_id')
    @classmethod
    def validate_national_id(cls, v):
        return _validate_national_id(v)


# Step 2 - personal details (all optional so the user can update partially)
class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_name: Optional[str] = None
    professional_name: Optional[str] = None
    religious_name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None

    @field_validator('national_id')
    @classmethod
    def validate_national_id(cls, v):
        return _validate_national_id(v)


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
    preferred_name: Optional[str] = None
    professional_name: Optional[str] = None
    religious_name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[date] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    national_id: Optional[str] = None
    profile_image: Optional[str] = None
    document_path: Optional[str] = None
    rejection_reason: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
