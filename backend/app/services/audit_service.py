from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import AppUser


def log_action(
    db: Session,
    actor: AppUser,
    action: str,
    access_request_id: Optional[int] = None,
    target_db_host: Optional[str] = None,
    target_db_service: Optional[str] = None,
    target_pdb: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    sql_executed: Optional[str] = None,
    rollback_sql: Optional[str] = None,
    result: Optional[str] = None,
    success: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor.id,
        actor_username=actor.username,
        action=action,
        access_request_id=access_request_id,
        target_db_host=target_db_host,
        target_db_service=target_db_service,
        target_pdb=target_pdb,
        before_state=before_state,
        after_state=after_state,
        sql_executed=sql_executed,
        rollback_sql=rollback_sql,
        result=result,
        success=success,
        details=details,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
