import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.access_log import AccessLog
from app.schemas.auth import RegisterRequest, UpdateProfileRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.admin import AccessLogResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.mail import send_password_reset_email
from app.core.config import settings
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

UPLOAD_DIR = "uploads/users"
UPLOAD_DIR_IMAGES = "uploads/profile-images"


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# Step 1: create account
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        first_name=body.first_name,
        middle_name=body.middle_name,
        last_name=body.last_name,
        preferred_name=body.preferred_name,
        professional_name=body.professional_name,
        religious_name=body.religious_name,
        nationality=body.nationality,
        birth_date=body.birth_date,
        phone_number=body.phone_number,
        location=body.location,
        education=body.education,
        national_id=body.national_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Step 2: fill in personal details (must be logged in)
@router.put("/profile", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    incoming = body.model_dump(exclude_none=True)
    for field, value in incoming.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


# Step 3 (optional): upload identity document
@router.post("/upload-document", response_model=UserResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and PDF files are allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # store as a URL path so the frontend can fetch it directly
    current_user.document_path = f"/uploads/users/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/upload-profile-image", response_model=UserResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")

    os.makedirs(UPLOAD_DIR_IMAGES, exist_ok=True)

    filename = f"{current_user.id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR_IMAGES, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    current_user.profile_image = f"/uploads/profile-images/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.post("/resubmit", response_model=UserResponse)
def resubmit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.is_active:
        raise HTTPException(status_code=400, detail="Account is not in a rejected state")
    current_user.is_active = True
    current_user.rejection_reason = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/forgot-password")
def forgot_password(body: dict = Body(...), db: Session = Depends(get_db)):
    email = body.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == email).first()
    # Always return 200 so we don't reveal whether an email is registered
    if not user:
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    name = user.first_name or user.username
    reset_link = f"{settings.FRONTEND_URL}/user/reset-password.html?token={token}"
    try:
        send_password_reset_email(user.email, reset_link, name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(body: dict = Body(...), db: Session = Depends(get_db)):
    token = body.get("token", "").strip()
    new_pw = body.get("new_password", "")

    if not token:
        raise HTTPException(status_code=400, detail="Reset token is required")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")

    user.hashed_password = hash_password(new_pw)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successfully. You can now log in."}


@router.put("/change-password")
def change_password(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_pw = body.get("current_password", "")
    new_pw = body.get("new_password", "")

    if not verify_password(current_pw, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(new_pw) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.hashed_password = hash_password(new_pw)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/access-logs", response_model=List[AccessLogResponse])
def my_access_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AccessLog)
        .filter(AccessLog.user_id == current_user.id)
        .order_by(AccessLog.created_at.desc())
        .all()
    )
