from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models import AppUser, AppRole
from app.routers import (
    auth_router, users_router, inventory_router,
    requests_router, approvals_router, execution_router, audit_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (also handled by Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    yield


def _seed_admin():
    """Create the initial admin user if no users exist."""
    db: Session = SessionLocal()
    try:
        if db.query(AppUser).count() == 0:
            admin = AppUser(
                username=settings.INITIAL_ADMIN_USERNAME,
                email="admin@example.com",
                full_name="System Administrator",
                role=AppRole.admin,
                hashed_password=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(inventory_router, prefix=API_PREFIX)
app.include_router(requests_router, prefix=API_PREFIX)
app.include_router(approvals_router, prefix=API_PREFIX)
app.include_router(execution_router, prefix=API_PREFIX)
app.include_router(audit_router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
