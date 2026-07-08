from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    actor_id = Column(Integer, ForeignKey("app_users.id"), nullable=True)
    actor_username = Column(String(64), nullable=False)  # denormalised for immutability

    # What action was performed
    action = Column(String(128), nullable=False)

    # Which request this relates to (optional)
    access_request_id = Column(Integer, ForeignKey("access_requests.id"), nullable=True)

    # Target database info
    target_db_host = Column(String(255), nullable=True)
    target_db_service = Column(String(255), nullable=True)
    target_pdb = Column(String(255), nullable=True)

    # State snapshot
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)

    # SQL evidence
    sql_executed = Column(Text, nullable=True)
    rollback_sql = Column(Text, nullable=True)

    # Result
    result = Column(Text, nullable=True)
    success = Column(String(8), nullable=False, default="unknown")  # "success", "failure", "unknown"

    # Additional metadata
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    actor = relationship("AppUser", back_populates="audit_logs")
    access_request = relationship("AccessRequest", back_populates="audit_logs")
