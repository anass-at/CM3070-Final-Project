"""
Shared fixtures for all tests.

Uses SQLite in-memory (with StaticPool) instead of MySQL so the suite runs
without a running database server.  The engine patch must happen before any
app code imports app.db.session, so the order of imports here is deliberate.
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# ── 1. Build a SQLite in-memory engine ───────────────────────────────────────
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# ── 2. Patch app.db.session BEFORE main.py is imported ───────────────────────
import app.db.session as _session_mod          # noqa: E402
_session_mod.engine = _test_engine
_session_mod.SessionLocal = _TestingSession

# ── 3. Now import app code (main.py's create_all uses the patched engine) ────
from main import app                                    # noqa: E402
from app.db.base import Base                           # noqa: E402
from app.db.session import get_db                      # noqa: E402
from app.core.security import hash_password, create_access_token  # noqa: E402
from app.models.user import User                       # noqa: E402
from app.models.company import Company                 # noqa: E402


# ── Schema lifecycle: fresh tables for every test ────────────────────────────
@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


# ── Database session ──────────────────────────────────────────────────────────
@pytest.fixture
def db():
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()


# ── HTTP test client wired to the test DB session ────────────────────────────
@pytest.fixture
def client(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Model fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def citizen(db):
    u = User(
        email="citizen@test.com",
        username="citizen_user",
        hashed_password=hash_password("Password123!"),
        first_name="John",
        middle_name="Michael",
        last_name="Doe",
        preferred_name="Johnny",
        professional_name="J. Doe",
        religious_name="Yusuf",
        nationality="British",
        birth_date=date(1990, 3, 15),
        phone_number="+447911123456",
        location="London",
        education="BSc Computer Science",
        national_id="12345678",
        is_active=True,
        is_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def unverified_citizen(db):
    u = User(
        email="unverified@test.com",
        username="unverified_user",
        hashed_password=hash_password("Password123!"),
        first_name="Jane",
        last_name="Smith",
        national_id="87654321",
        is_active=True,
        is_verified=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def citizen_token(citizen):
    return create_access_token({"sub": str(citizen.id)})


@pytest.fixture
def admin_user(db):
    u = User(
        email="admin@natid.gov",
        username="admin",
        hashed_password=hash_password("Admin1234!"),
        first_name="System",
        last_name="Admin",
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def admin_token(admin_user):
    return create_access_token({"sub": str(admin_user.id)})


@pytest.fixture
def company(db):
    c = Company(
        name="Test Bank",
        email="bank@test.com",
        hashed_password=hash_password("CompanyPass123!"),
        requested_scopes='[{"scope":"name:legal","justification":"KYC compliance"}]',
        approved_scopes="",
        is_approved=False,
        is_active=True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def approved_company(db):
    c = Company(
        name="Approved Bank",
        email="approved@test.com",
        hashed_password=hash_password("CompanyPass123!"),
        requested_scopes='[{"scope":"name:legal","justification":"KYC"}]',
        approved_scopes="name:legal,profile:basic",
        is_approved=True,
        is_active=True,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    # Set hydra_client_id to match the actual DB-assigned ID
    c.hydra_client_id = f"company_{c.id}"
    c.hydra_client_secret = "secret_abc123"
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def company_token(approved_company):
    return create_access_token({
        "sub": f"company_{approved_company.id}",
        "scopes": ["name:legal", "profile:basic"],
        "type": "company",
    })
