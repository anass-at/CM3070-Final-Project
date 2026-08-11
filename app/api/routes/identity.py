from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.models.company import Company
from app.models.access_log import AccessLog
from app.core.hydra import introspect_token
from app.core.scopes import SCOPE_FIELDS

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:4444/oauth2/token")


@router.get("/{national_id}")
def get_identity(
    national_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # Validate token with Hydra
    try:
        token_data = introspect_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {e}")

    if not token_data.get("active"):
        raise HTTPException(status_code=401, detail="Token is inactive or expired")

    # Extract client identity and scopes from Hydra response
    client_id = token_data.get("client_id", "")
    scope_string = token_data.get("scope", "")
    scopes = [s for s in scope_string.split(" ") if s]

    # Resolve company from Hydra client_id
    try:
        company_id = int(client_id.replace("company_", ""))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid client identity")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company or not company.is_approved:
        raise HTTPException(status_code=403, detail="Company not approved")

    # Resolve user by national_id and check they are verified
    user = db.query(User).filter(User.national_id == national_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="User identity not verified")

    # Build the response — handle computed scopes first, then regular field scopes
    result = {"national_id": user.national_id}

    for scope in scopes:
        if scope == "name:full_name":
            parts = []
            if user.first_name:
                parts.append(user.first_name)
            if user.middle_name:
                parts.append(user.middle_name)
            if user.last_name:
                parts.append(user.last_name)
            if parts:
                result["full_name"] = " ".join(parts)
        else:
            for field in SCOPE_FIELDS.get(scope, []):
                value = getattr(user, field, None)
                if value is not None:
                    result[field] = str(value) if isinstance(value, date) else value

    # Log the access
    db.add(AccessLog(
        company_id=company.id,
        company_name=company.name,
        user_id=user.id,
        scope_used=" ".join(scopes),
        endpoint=f"/api/v1/identity/{national_id}",
        status_code=200,
    ))
    db.commit()

    return result
