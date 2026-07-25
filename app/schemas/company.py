from pydantic import BaseModel, EmailStr
from typing import Optional


class CompanyRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    contact_email: Optional[EmailStr] = None
    description: Optional[str] = None


class CompanyLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    is_approved: bool
    approved_scopes: str

    model_config = {"from_attributes": True}
