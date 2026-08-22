"""
Create the first admin user.

Usage (from project root):
    python -m scripts.seed_admin

Or with custom credentials:
    ADMIN_EMAIL=admin@natid.local ADMIN_PASSWORD=changeme python -m scripts.seed_admin
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.core.security import hash_password

import app.models.user       # noqa
import app.models.company    # noqa
import app.models.access_log # noqa

Base.metadata.create_all(bind=engine)

ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL",    "admin@natid.gov")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin1234!")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

db = SessionLocal()

try:
    existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    if existing:
        print(f"Admin already exists: {ADMIN_EMAIL}")
        sys.exit(0)

    admin = User(
        email=ADMIN_EMAIL,
        username=ADMIN_USERNAME,
        hashed_password=hash_password(ADMIN_PASSWORD),
        first_name="System",
        last_name="Admin",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin created successfully.")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print(f"  Username: {ADMIN_USERNAME}")
    print()
    print("Change the password after first login!")
finally:
    db.close()
