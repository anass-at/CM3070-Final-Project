from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # account info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # user | third_party | admin

    # personal details
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    preferred_name = Column(String(100), nullable=True)      # scope: name:preferred
    professional_name = Column(String(100), nullable=True)   # scope: name:professional
    religious_name = Column(String(100), nullable=True)      # scope: name:religious
    nationality = Column(String(100), nullable=True)         # scope: profile:basic
    birth_date = Column(Date, nullable=True)
    phone_number = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    education = Column(String(255), nullable=True)
    national_id = Column(String(100), nullable=True)

    # uploaded files
    profile_image = Column(String(500), nullable=True)
    document_path = Column(String(500), nullable=True)

    rejection_reason = Column(String(1000), nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    reset_token = Column(String(100), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
