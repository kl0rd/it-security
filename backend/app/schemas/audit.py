from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_username: str
    action: str
    access_request_id: Optional[int] = None
    target_db_host: Optional[str] = None
    target_db_service: Optional[str] = None
    target_pdb: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    sql_executed: Optional[str] = None
    rollback_sql: Optional[str] = None
    result: Optional[str] = None
    success: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
