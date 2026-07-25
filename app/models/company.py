from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # scopes the admin approved - stored as comma separated string
    # example: "name:legal,profile:basic"
    approved_scopes = Column(String(500), default="")

    is_approved = Column(Boolean, default=False)  # admin has to approve first
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
