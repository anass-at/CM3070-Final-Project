import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password

EMAIL = "admin@natid.gov"
USERNAME = "admin"
PASSWORD = "admin123"

db = SessionLocal()

existing = db.query(User).filter(User.email == EMAIL).first()
if existing:
    print(f"Admin already exists: {EMAIL}")
else:
    admin = User(
        email=EMAIL,
        username=USERNAME,
        hashed_password=hash_password(PASSWORD),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin created — email: {EMAIL}  password: {PASSWORD}")

db.close()
