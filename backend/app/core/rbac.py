from typing import List
from fastapi import HTTPException, status
from app.models.user import AppRole


ROLE_PERMISSIONS = {
    AppRole.admin: {
        "manage_users", "view_inventory", "create_request", "approve_request",
        "execute_request", "view_audit", "manage_databases",
    },
    AppRole.approver: {
        "view_inventory", "create_request", "approve_request", "view_audit",
    },
    AppRole.requester: {
        "view_inventory", "create_request", "view_audit",
    },
    AppRole.auditor: {
        "view_inventory", "view_audit",
    },
}


def require_permission(user_role: AppRole, permission: str) -> None:
    allowed = ROLE_PERMISSIONS.get(user_role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user_role}' does not have permission: {permission}",
        )


def has_permission(user_role: AppRole, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user_role, set())
