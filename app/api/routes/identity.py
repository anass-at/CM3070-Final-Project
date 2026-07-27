from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.access_log import AccessLog
from app.core.security import decode_access_token
from app.core.scopes import SCOPE_FIELDS

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/company/login")


@router.get("/{user_id}")
def get_identity(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # Validate company token
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "company":
            raise HTTPException(status_code=401, detail="Not a company token")
        company_id = int(str(payload["sub"]).replace("company_", ""))
        scopes = payload.get("scopes", [])
    except (JWTError, ValueError) as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Check company is still approved
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.is_approved:
        raise HTTPException(status_code=403, detail="Company not approved")

    # Check user exists and is verified
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User identity not verified")

    # Build allowed fields from token scopes
    allowed_fields = []
    for scope in scopes:
        allowed_fields.extend(SCOPE_FIELDS.get(scope, []))

    # Return only allowed fields
    result = {"user_id": user.id}
    for field in allowed_fields:
        value = getattr(user, field, None)
        if value is not None:
            result[field] = str(value) if isinstance(value, date) else value

    # Write access log
    db.add(AccessLog(
        company_id=company.id,
        company_name=company.name,
        user_id=user.id,
        scope_used=",".join(scopes),
        endpoint=f"/api/v1/identity/{user_id}",
        status_code=200,
    ))
    db.commit()

    return result
