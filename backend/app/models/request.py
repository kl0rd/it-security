import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class RequestType(str, enum.Enum):
    create_user = "create_user"
    drop_user = "drop_user"
    lock_user = "lock_user"
    unlock_user = "unlock_user"
    grant_role = "grant_role"
    revoke_role = "revoke_role"
    grant_system_privilege = "grant_system_privilege"
    revoke_system_privilege = "revoke_system_privilege"
    grant_object_privilege = "grant_object_privilege"
    revoke_object_privilege = "revoke_object_privilege"


class RequestStatus(str, enum.Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    executed = "executed"
    failed = "failed"
    rolled_back = "rolled_back"


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.draft)

    # Target database connection info
    target_db_host = Column(String(255), nullable=False)
    target_db_port = Column(Integer, nullable=False, default=1521)
    target_db_service = Column(String(255), nullable=False)
    target_pdb = Column(String(255), nullable=True)

    # Parameters specific to the request type (stored as JSON)
    # e.g. {"username": "JOHN", "profile": "DEFAULT", "password_required": true}
    parameters = Column(JSON, nullable=False, default=dict)

    # Generated SQL
    execution_sql = Column(Text, nullable=True)
    rollback_sql = Column(Text, nullable=True)

    # Execution output
    execution_output = Column(Text, nullable=True)
    execution_error = Column(Text, nullable=True)

    # People
    requester_id = Column(Integer, ForeignKey("app_users.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    executor_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Relationships
    requester = relationship("AppUser", foreign_keys=[requester_id], back_populates="submitted_requests")
    approver = relationship("AppUser", foreign_keys=[approver_id], back_populates="approved_requests")
    executor = relationship("AppUser", foreign_keys=[executor_id], back_populates="executed_requests")
    audit_logs = relationship("AuditLog", back_populates="access_request")
