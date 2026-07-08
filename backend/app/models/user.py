import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


class AppRole(str, enum.Enum):
    admin = "admin"
    approver = "approver"
    requester = "requester"
    auditor = "auditor"


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(AppRole), nullable=False, default=AppRole.requester)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submitted_requests = relationship(
        "AccessRequest", foreign_keys="AccessRequest.requester_id", back_populates="requester"
    )
    approved_requests = relationship(
        "AccessRequest", foreign_keys="AccessRequest.approver_id", back_populates="approver"
    )
    executed_requests = relationship(
        "AccessRequest", foreign_keys="AccessRequest.executor_id", back_populates="executor"
    )
    audit_logs = relationship("AuditLog", back_populates="actor")
