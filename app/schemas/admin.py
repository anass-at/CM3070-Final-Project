import json
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime

from app.schemas.company import ScopeJustification


class AdminUserResponse(BaseModel):
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
    is_verified: bool
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminCompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    company_type: Optional[str] = None
    commercial_number: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    document_path: Optional[str] = None
    requested_scopes: Optional[List[ScopeJustification]] = None
    approved_scopes: Optional[str] = None
    hydra_client_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_approved: bool
    is_active: bool
    created_at: Optional[datetime] = None

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


class ApproveCompanyResponse(AdminCompanyResponse):
    """Returned only on approval — includes the client secret (shown once)."""
    hydra_client_secret: Optional[str] = None


class ApproveCompanyRequest(BaseModel):
    scopes: List[str]  # just scope name strings — admin picks which to approve


class RejectRequest(BaseModel):
    reason: Optional[str] = None


class AccessLogResponse(BaseModel):
    id: int
    company_id: int
    company_name: str
    user_id: int
    scope_used: str
    endpoint: str
    status_code: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
