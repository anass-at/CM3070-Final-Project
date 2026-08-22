from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.access_log import AccessLog
from app.core.security import decode_access_token, hash_password
from app.core.scopes import ALL_SCOPES
from app.schemas.admin import (
    AdminUserResponse,
    AdminCompanyResponse,
    ApproveCompanyResponse,
    ApproveCompanyRequest,
    RejectRequest,
    AccessLogResponse,
)
from app.core.hydra import create_hydra_client, update_hydra_client, delete_hydra_client

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@router.get("/stats")
def get_stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    all_users = db.query(User).filter(User.role != "admin").all()
    all_companies = db.query(Company).all()

    # complete profile = has first_name, last_name, national_id, document_path
    def profile_complete(u):
        return bool(u.first_name and u.last_name and u.national_id and u.document_path)

    total_users       = len(all_users)
    verified_users    = sum(1 for u in all_users if u.is_verified)
    rejected_users    = sum(1 for u in all_users if not u.is_active)
    pending_users     = sum(1 for u in all_users if profile_complete(u) and not u.is_verified and u.is_active)

    total_companies    = len(all_companies)
    approved_companies = sum(1 for c in all_companies if c.is_approved)
    rejected_companies = sum(1 for c in all_companies if not c.is_active)
    pending_companies  = sum(1 for c in all_companies if not c.is_approved and c.is_active)

    # approved companies that have requested scopes not yet in approved_scopes
    def has_scope_update(c):
        if not c.is_approved:
            return False
        approved = set(s.strip() for s in (c.approved_scopes or "").split(",") if s.strip())
        requested = set(s.strip() for s in (c.requested_scopes or "").split(",") if s.strip())
        return bool(requested - approved)

    scope_updates = sum(1 for c in all_companies if has_scope_update(c))

    return {
        "total_users":        total_users,
        "verified_users":     verified_users,
        "pending_users":      pending_users,
        "rejected_users":     rejected_users,
        "total_companies":    total_companies,
        "approved_companies": approved_companies,
        "pending_companies":  pending_companies,
        "rejected_companies": rejected_companies,
        "scope_updates":      scope_updates,
    }


# --- Users ---

@router.get("/users", response_model=List[AdminUserResponse])
def list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    # only show users with a complete profile: first name, last name, national ID, and uploaded document
    return db.query(User).filter(
        User.role != "admin",
        User.first_name.isnot(None), User.first_name != "",
        User.last_name.isnot(None),  User.last_name != "",
        User.national_id.isnot(None), User.national_id != "",
        User.document_path.isnot(None), User.document_path != "",
    ).all()


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/verify", response_model=AdminUserResponse)
def verify_user(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reject", response_model=AdminUserResponse)
def reject_user(user_id: int, body: RejectRequest, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = False
    user.is_active = False
    user.rejection_reason = body.reason or None
    db.commit()
    db.refresh(user)
    return user


# --- Companies ---

@router.get("/companies", response_model=List[AdminCompanyResponse])
def list_companies(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(Company).all()


@router.get("/companies/{company_id}", response_model=AdminCompanyResponse)
def get_company(company_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/companies/{company_id}/approve", response_model=ApproveCompanyResponse)
def approve_company(
    company_id: int,
    body: ApproveCompanyRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    import json as _json
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not body.scopes:
        raise HTTPException(status_code=400, detail="At least one scope must be approved")

    invalid = [s for s in body.scopes if s not in ALL_SCOPES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {invalid}")

    # Warn if admin is approving scopes that were never requested
    try:
        requested = {item["scope"] for item in _json.loads(company.requested_scopes or "[]")}
    except Exception:
        requested = set()
    not_requested = [s for s in body.scopes if s not in requested]
    if not_requested and requested:
        raise HTTPException(
            status_code=400,
            detail=f"Scopes not requested by this company: {not_requested}"
        )

    # Create or update Hydra OAuth2 client
    try:
        if company.hydra_client_id:
            update_hydra_client(company.hydra_client_id, body.scopes)
            client_secret = company.hydra_client_secret
        else:
            client_id, client_secret = create_hydra_client(company.id, body.scopes)
            company.hydra_client_id = client_id
            company.hydra_client_secret = client_secret
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hydra error: {e}")

    company.approved_scopes = ",".join(body.scopes)
    company.is_approved = True
    company.is_active = True
    db.commit()
    db.refresh(company)

    # Build response and expose the secret once so admin can pass it to the company
    response = ApproveCompanyResponse.model_validate(company)
    response.hydra_client_secret = client_secret
    return response


@router.post("/companies/{company_id}/reject", response_model=AdminCompanyResponse)
def reject_company(
    company_id: int,
    body: RejectRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Remove Hydra client if it exists
    if company.hydra_client_id:
        try:
            delete_hydra_client(company.hydra_client_id)
        except Exception:
            pass
        company.hydra_client_id = None
        company.hydra_client_secret = None

    company.is_approved = False
    company.is_active = False
    company.approved_scopes = ""
    company.rejection_reason = body.reason or None
    db.commit()
    db.refresh(company)
    return company


# --- Access Logs ---

@router.get("/access-logs", response_model=List[AccessLogResponse])
def list_access_logs(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(AccessLog).order_by(AccessLog.created_at.desc()).all()


@router.get("/access-logs/company/{company_id}", response_model=List[AccessLogResponse])
def logs_by_company(
    company_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(AccessLog).filter(AccessLog.company_id == company_id).order_by(AccessLog.created_at.desc()).all()


@router.get("/access-logs/user/{user_id}", response_model=List[AccessLogResponse])
def logs_by_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(AccessLog).filter(AccessLog.user_id == user_id).order_by(AccessLog.created_at.desc()).all()
