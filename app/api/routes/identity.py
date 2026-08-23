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
    # Track values for the access log — defaults represent an anonymous failed attempt
    log_company_id   = 0
    log_company_name = "unknown"
    log_user_id      = 0
    log_scopes       = ""
    log_status       = 500

    try:
        # Validate token with Hydra
        try:
            token_data = introspect_token(token)
        except Exception as e:
            log_status = 401
            raise HTTPException(status_code=401, detail=f"Token validation failed: {e}")

        if not token_data.get("active"):
            log_status = 401
            raise HTTPException(status_code=401, detail="Token is inactive or expired")

        client_id   = token_data.get("client_id", "")
        scope_string = token_data.get("scope", "")
        scopes      = [s for s in scope_string.split(" ") if s]
        log_scopes  = " ".join(scopes)

        try:
            company_id = int(client_id.replace("company_", ""))
        except ValueError:
            log_status = 401
            raise HTTPException(status_code=401, detail="Invalid client identity")

        company = db.query(Company).filter(Company.id == company_id).first()
        if not company or not company.is_approved:
            log_status = 403
            raise HTTPException(status_code=403, detail="Company not approved")

        log_company_id   = company.id
        log_company_name = company.name

        user = db.query(User).filter(User.national_id == national_id).first()
        if not user:
            log_status = 404
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_verified:
            log_status = 403
            raise HTTPException(status_code=403, detail="User identity not verified")

        log_user_id = user.id

        # Build the response — only fields within the token's approved scopes.
        # national_id is only returned if identity:national_id is explicitly granted.
        result = {}
        for scope in scopes:
            for field in SCOPE_FIELDS.get(scope, []):
                value = getattr(user, field, None)
                if value is not None:
                    result[field] = str(value) if isinstance(value, date) else value

        log_status = 200
        return {"scopes_used": scopes, "data": result}

    finally:
        try:
            db.add(AccessLog(
                company_id=log_company_id,
                company_name=log_company_name,
                user_id=log_user_id,
                scope_used=log_scopes,
                endpoint=f"/api/v1/identity/{national_id}",
                status_code=log_status,
            ))
            db.commit()
        except Exception:
            db.rollback()
