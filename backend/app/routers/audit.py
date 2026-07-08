from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import AppUser
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    actor_username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    access_request_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_audit")),
):
    q = db.query(AuditLog)
    if actor_username:
        q = q.filter(AuditLog.actor_username == actor_username)
    if action:
        q = q.filter(AuditLog.action == action)
    if access_request_id is not None:
        q = q.filter(AuditLog.access_request_id == access_request_id)
    return q.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{log_id}", response_model=AuditLogOut)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_audit")),
):
    from fastapi import HTTPException
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log
