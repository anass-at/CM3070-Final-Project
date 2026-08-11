from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password
from app.core.hydra import (
    get_login_request, accept_login_request, reject_login_request,
    get_consent_request, accept_consent_request, reject_consent_request,
)

router = APIRouter()


class LoginChallengeRequest(BaseModel):
    login_challenge: str
    email: str
    password: str


class ConsentAcceptRequest(BaseModel):
    consent_challenge: str
    grant_scopes: list[str]


class ConsentRejectRequest(BaseModel):
    consent_challenge: str


@router.get("/login")
def hydra_get_login(login_challenge: str):
    """Return info about the login challenge so the frontend can render the form."""
    try:
        data = get_login_request(login_challenge)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid login challenge: {e}")
    return {
        "client_name": data.get("client", {}).get("client_name") or data.get("client", {}).get("client_id", ""),
        "requested_scope": data.get("requested_scope", []),
        "skip": data.get("skip", False),
        "subject": data.get("subject", ""),
    }


@router.post("/login")
def hydra_accept_login(body: LoginChallengeRequest, db: Session = Depends(get_db)):
    """Verify user credentials and tell Hydra to accept the login."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.national_id:
        raise HTTPException(status_code=403, detail="Complete your profile before authorizing third-party access")

    try:
        redirect_to = accept_login_request(body.login_challenge, subject=user.national_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Hydra error: {e}")

    return {"redirect_to": redirect_to}


@router.post("/login/reject")
def hydra_reject_login(body: dict, db: Session = Depends(get_db)):
    try:
        redirect_to = reject_login_request(body.get("login_challenge", ""))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"redirect_to": redirect_to}


@router.get("/consent")
def hydra_get_consent(consent_challenge: str):
    """Return info about the consent challenge so the frontend can render the consent form."""
    try:
        data = get_consent_request(consent_challenge)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid consent challenge: {e}")

    client = data.get("client", {})
    return {
        "client_name": client.get("client_name") or client.get("client_id", "Unknown"),
        "requested_scope": data.get("requested_scope", []),
        "subject": data.get("subject", ""),
        "skip": data.get("skip", False),
    }


@router.post("/consent/accept")
def hydra_accept_consent(body: ConsentAcceptRequest):
    try:
        redirect_to = accept_consent_request(body.consent_challenge, body.grant_scopes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Hydra error: {e}")
    return {"redirect_to": redirect_to}


@router.post("/consent/reject")
def hydra_reject_consent(body: ConsentRejectRequest):
    try:
        redirect_to = reject_consent_request(body.consent_challenge)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Hydra error: {e}")
    return {"redirect_to": redirect_to}
