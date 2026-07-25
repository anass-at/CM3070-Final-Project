from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import CompanyRegisterRequest, CompanyLoginRequest, CompanyResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/company/login")


# helper to get the company from the token
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


@router.post("/register", response_model=CompanyResponse, status_code=201)
def register_company(body: CompanyRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Company).filter(Company.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    company = Company(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        contact_email=body.contact_email,
        description=body.description,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/login")
def login_company(body: CompanyLoginRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.email == body.email).first()
    if not company or not verify_password(body.password, company.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not company.is_approved:
        raise HTTPException(status_code=403, detail="Your company account is pending admin approval")
    if not company.is_active:
        raise HTTPException(status_code=403, detail="This company account has been disabled")

    # put the approved scopes inside the token
    # when the company calls /identity/{user_id}, the scopes get checked
    scopes_list = [s.strip() for s in company.approved_scopes.split(",") if s.strip()]
    token = create_access_token({
        "sub": f"company_{company.id}",
        "scopes": scopes_list,
        "type": "company"
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "approved_scopes": scopes_list
    }


@router.get("/profile", response_model=CompanyResponse)
def get_company_profile(company: Company = Depends(get_current_company)):
    return company
