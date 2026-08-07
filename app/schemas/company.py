from pydantic import BaseModel, EmailStr
from typing import Optional, List


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


# Step 4 - request scopes with justification
class RequestScopesRequest(BaseModel):
    # list of scope names the company wants e.g. ["name:full", "profile:basic"]
    scopes: List[str]
    # explain why each scope is needed (one paragraph is fine)
    justification: str


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
    document_path: Optional[str] = None
    requested_scopes: Optional[str] = None
    scope_justification: Optional[str] = None
    is_approved: bool
    is_active: bool
    approved_scopes: str
    hydra_client_id: Optional[str] = None
    hydra_client_secret: Optional[str] = None

    model_config = {"from_attributes": True}
