import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import CompanyRegisterRequest, UpdateCompanyProfileRequest, RequestScopesRequest, CompanyLoginRequest, CompanyResponse
from app.core.scopes import ALL_SCOPES
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.hydra import exchange_authorization_code
from app.core.mail import send_password_reset_email
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/company/login")

UPLOAD_DIR = "uploads/companies"
UPLOAD_DIR_LOGOS = "uploads/company-logos"


def get_current_company(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Company:
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "company":
            raise HTTPException(status_code=401, detail="Not a company token")
        company_id = int(str(payload["sub"]).replace("company_", ""))
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=401, detail="Company not found")
        return company
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


# Step 1: create company account
@router.post("/register", response_model=CompanyResponse, status_code=201)
def register_company(body: CompanyRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Company).filter(Company.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    company = Company(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


# Step 2: fill in company details (must be logged in)
@router.put("/profile", response_model=CompanyResponse)
def update_company_profile(
    body: UpdateCompanyProfileRequest,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company


# Step 3 (optional): upload company registration document
@router.post("/upload-document", response_model=CompanyResponse)
async def upload_document(
    file: UploadFile = File(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{company.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    company.document_path = f"/uploads/companies/{filename}"
    db.commit()
    db.refresh(company)
    return company


@router.post("/upload-logo", response_model=CompanyResponse)
async def upload_logo(
    file: UploadFile = File(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")

    os.makedirs(UPLOAD_DIR_LOGOS, exist_ok=True)

    filename = f"{company.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR_LOGOS, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    company.logo = f"/uploads/company-logos/{filename}"
    db.commit()
    db.refresh(company)
    return company


# Resubmit after rejection — resets to pending so admin can review again
@router.post("/resubmit", response_model=CompanyResponse)
def resubmit_company(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if company.is_active:
        raise HTTPException(status_code=400, detail="Company is not in a rejected state")

    company.is_active = True
    company.rejection_reason = None
    db.commit()
    db.refresh(company)
    return company


# Step 4: request data scopes, each with its own justification (must be logged in)
@router.post("/request-scopes", response_model=CompanyResponse)
def request_scopes(
    body: RequestScopesRequest,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if not body.scopes:
        raise HTTPException(status_code=400, detail="At least one scope is required")

    invalid = [s.scope for s in body.scopes if s.scope not in ALL_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scopes: {invalid}. Valid scopes are: {ALL_SCOPES}"
        )
    for s in body.scopes:
        if not s.justification.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Justification for scope '{s.scope}' cannot be empty"
            )

    company.requested_scopes = json.dumps([s.model_dump() for s in body.scopes])
    db.commit()
    db.refresh(company)
    return company


@router.post("/login")
def login_company(body: CompanyLoginRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.email == body.email).first()
    if not company or not verify_password(body.password, company.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    scopes_list = [s.strip() for s in company.approved_scopes.split(",") if s.strip()]
    token = create_access_token({
        "sub": f"company_{company.id}",
        "scopes": scopes_list,
        "type": "company"
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "is_approved": company.is_approved,
        "approved_scopes": scopes_list
    }


@router.get("/profile", response_model=CompanyResponse)
def get_company_profile(company: Company = Depends(get_current_company)):
    return company


@router.post("/forgot-password")
def company_forgot_password(body: dict = Body(...), db: Session = Depends(get_db)):
    email = body.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    company = db.query(Company).filter(Company.email == email).first()
    if not company:
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    company.reset_token = token
    company.reset_token_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/company/reset-password.html?token={token}"
    try:
        send_password_reset_email(company.email, reset_link, company.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def company_reset_password(body: dict = Body(...), db: Session = Depends(get_db)):
    token = body.get("token", "").strip()
    new_pw = body.get("new_password", "")

    if not token:
        raise HTTPException(status_code=400, detail="Reset token is required")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    company = db.query(Company).filter(Company.reset_token == token).first()
    if not company:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    if company.reset_token_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")

    company.hashed_password = hash_password(new_pw)
    company.reset_token = None
    company.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully. You can now log in."}


@router.post("/oauth/exchange")
def exchange_code(
    body: dict = Body(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Exchange an OAuth2 authorization code for tokens using the company's Hydra client credentials."""
    if not company.hydra_client_id or not company.hydra_client_secret:
        raise HTTPException(status_code=400, detail="Company does not have an active OAuth2 client")

    code = body.get("code", "")
    redirect_uri = body.get("redirect_uri", "")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri is required")

    try:
        token_data = exchange_authorization_code(
            company.hydra_client_id,
            company.hydra_client_secret,
            code,
            redirect_uri,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    return token_data


@router.put("/change-password")
def change_company_password(
    body: dict = Body(...),
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    current_pw = body.get("current_password", "")
    new_pw = body.get("new_password", "")

    if not verify_password(current_pw, company.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    company.hashed_password = hash_password(new_pw)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout_company(company: Company = Depends(get_current_company)):
    return {"message": "Logged out successfully"}
