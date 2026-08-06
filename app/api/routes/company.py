import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import CompanyRegisterRequest, UpdateCompanyProfileRequest, RequestScopesRequest, CompanyLoginRequest, CompanyResponse
from app.core.scopes import ALL_SCOPES
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/company/login")

UPLOAD_DIR = "uploads/companies"


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

    company.document_path = file_path
    db.commit()
    db.refresh(company)
    return company


# Step 4: request data scopes with justification (must be logged in)
@router.post("/request-scopes", response_model=CompanyResponse)
def request_scopes(
    body: RequestScopesRequest,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    # check that all requested scopes are valid
    invalid = [s for s in body.scopes if s not in ALL_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scopes: {invalid}. Valid scopes are: {ALL_SCOPES}"
        )
    if not body.justification.strip():
        raise HTTPException(status_code=400, detail="Justification cannot be empty")

    company.requested_scopes = ",".join(body.scopes)
    company.scope_justification = body.justification
    db.commit()
    db.refresh(company)
    return company


@router.post("/login")
def login_company(body: CompanyLoginRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.email == body.email).first()
    if not company or not verify_password(body.password, company.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not company.is_active:
        raise HTTPException(status_code=403, detail="This company account has been disabled")

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


@router.post("/logout")
def logout_company(company: Company = Depends(get_current_company)):
    return {"message": "Logged out successfully"}
