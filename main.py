from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth
from app.api.routes import company
from app.api.routes import admin
from app.api.routes import identity
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

import app.models.user       # noqa: F401
import app.models.company    # noqa: F401
import app.models.access_log # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Identity & Profile Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix=f"{settings.API_V1_STR}/auth",     tags=["auth"])
app.include_router(company.router,  prefix=f"{settings.API_V1_STR}/company",  tags=["company"])
app.include_router(admin.router,    prefix=f"{settings.API_V1_STR}/admin",    tags=["admin"])
app.include_router(identity.router, prefix=f"{settings.API_V1_STR}/identity", tags=["identity"])


@app.get("/")
def root():
    return {"message": "Identity API is running"}

