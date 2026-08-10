from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    # account info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # company details
    commercial_number = Column(String(100), nullable=True)
    company_type = Column(String(100), nullable=True)  # bank, hospital, government, etc.
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)

    # uploaded files
    logo = Column(String(500), nullable=True)
    document_path = Column(String(500), nullable=True)

    # scopes the company requested - comma separated, filled in step 4
    requested_scopes = Column(String(500), default="")

    # why the company needs each scope (free text written by the company)
    scope_justification = Column(Text, nullable=True)

    # scopes the admin approved - comma separated e.g. "name:full,profile:basic"
    approved_scopes = Column(String(500), default="")

    # set when admin approves — used to get OAuth2 tokens from Hydra
    hydra_client_id = Column(String(100), nullable=True)
    hydra_client_secret = Column(String(100), nullable=True)

    rejection_reason = Column(String(1000), nullable=True)

    is_approved = Column(Boolean, default=False)  # admin must approve first
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
