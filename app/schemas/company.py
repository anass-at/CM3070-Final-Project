import json
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List


class ScopeJustification(BaseModel):
    scope: str
    justification: str


# Step 1 - just the account credentials
class CompanyRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


# Step 2 - company details (all optional so the company can update partially)
class UpdateCompanyProfileRequest(BaseModel):
    commercial_number: Optional[str] = None
    company_type: Optional[str] = None  # bank, hospital, government, etc.
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None


# Step 4 - request scopes, each with its own justification
class RequestScopesRequest(BaseModel):
    scopes: List[ScopeJustification]


class CompanyLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    commercial_number: Optional[str] = None
    company_type: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    document_path: Optional[str] = None
    requested_scopes: Optional[List[ScopeJustification]] = None
    rejection_reason: Optional[str] = None
    is_approved: bool
    is_active: bool
    approved_scopes: str
    hydra_client_id: Optional[str] = None
    hydra_client_secret: Optional[str] = None

    @field_validator('requested_scopes', mode='before')
    @classmethod
    def parse_requested_scopes(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except (json.JSONDecodeError, ValueError):
                return []
        return v or []

    model_config = {"from_attributes": True}
