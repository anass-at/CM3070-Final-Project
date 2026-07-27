from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.base import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    scope_used = Column(String(500), nullable=False)
    endpoint = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
