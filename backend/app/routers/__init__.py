from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.inventory import router as inventory_router
from app.routers.requests import router as requests_router
from app.routers.approvals import router as approvals_router
from app.routers.execution import router as execution_router
from app.routers.audit import router as audit_router

__all__ = [
    "auth_router",
    "users_router",
    "inventory_router",
    "requests_router",
    "approvals_router",
    "execution_router",
    "audit_router",
]
