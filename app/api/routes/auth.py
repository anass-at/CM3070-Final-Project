import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.access_log import AccessLog
from app.schemas.auth import RegisterRequest, UpdateProfileRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.admin import AccessLogResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
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
    for field, value in body.model_dump(exclude_none=True).items():
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
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.get("/access-logs", response_model=List[AccessLogResponse])
def my_access_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AccessLog)
        .filter(AccessLog.user_id == current_user.id)
        .order_by(AccessLog.created_at.desc())
        .all()
    )
