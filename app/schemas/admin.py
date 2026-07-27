from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class AdminUserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    national_id: Optional[str] = None
    document_path: Optional[str] = None
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
    document_path: Optional[str] = None
    requested_scopes: Optional[str] = None
    scope_justification: Optional[str] = None
    approved_scopes: Optional[str] = None
    is_approved: bool
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApproveCompanyRequest(BaseModel):
    scopes: List[str]


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
