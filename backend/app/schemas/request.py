from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel
from app.models.request import RequestType, RequestStatus


class AccessRequestBase(BaseModel):
    title: str
    description: Optional[str] = None
    request_type: RequestType
    target_db_host: str
    target_db_port: int = 1521
    target_db_service: str
    target_pdb: Optional[str] = None
    parameters: Dict[str, Any] = {}


class AccessRequestCreate(AccessRequestBase):
    pass


class AccessRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class AccessRequestOut(AccessRequestBase):
    id: int
    status: RequestStatus
    execution_sql: Optional[str] = None
    rollback_sql: Optional[str] = None
    execution_output: Optional[str] = None
    execution_error: Optional[str] = None
    requester_id: int
    approver_id: Optional[int] = None
    executor_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


class GeneratedSQL(BaseModel):
    execution_sql: str
    rollback_sql: str
