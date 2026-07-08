"""Unit tests for the AuditLog model and audit_service."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestAuditLogModel:
    """Test the AuditLog SQLAlchemy model structure."""

    def test_audit_log_fields_exist(self):
        from app.models.audit import AuditLog
        columns = {c.name for c in AuditLog.__table__.columns}
        required = {
            "id", "actor_id", "actor_username", "action",
            "access_request_id", "target_db_host", "target_db_service",
            "target_pdb", "before_state", "after_state",
            "sql_executed", "rollback_sql", "result", "success",
            "details", "created_at",
        }
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_audit_log_relationships(self):
        from app.models.audit import AuditLog
        rel_names = {r.key for r in AuditLog.__mapper__.relationships}
        assert "actor" in rel_names
        assert "access_request" in rel_names

    def test_audit_log_creation(self):
        from app.models.audit import AuditLog
        log = AuditLog(
            actor_username="admin",
            action="TEST_ACTION",
            success="success",
        )
        assert log.actor_username == "admin"
        assert log.action == "TEST_ACTION"
        assert log.success == "success"

    def test_audit_log_all_fields(self):
        from app.models.audit import AuditLog
        now = datetime.utcnow()
        log = AuditLog(
            actor_id=1,
            actor_username="alice",
            action="EXECUTE_REQUEST",
            access_request_id=42,
            target_db_host="oracle.example.com",
            target_db_service="ORCLPDB1",
            target_pdb="MYPDB",
            before_state={"account_status": "OPEN"},
            after_state={"account_status": "LOCKED"},
            sql_executed="ALTER USER FOO ACCOUNT LOCK",
            rollback_sql="ALTER USER FOO ACCOUNT UNLOCK",
            result="Statement executed successfully.",
            success="success",
            details={"request_type": "lock_user"},
            created_at=now,
        )
        assert log.actor_id == 1
        assert log.actor_username == "alice"
        assert log.target_db_host == "oracle.example.com"
        assert log.before_state == {"account_status": "OPEN"}
        assert log.after_state == {"account_status": "LOCKED"}
        assert log.sql_executed == "ALTER USER FOO ACCOUNT LOCK"
        assert log.rollback_sql == "ALTER USER FOO ACCOUNT UNLOCK"
        assert log.success == "success"


class TestAuditService:
    """Test the audit_service.log_action function."""

    def test_log_action_creates_entry(self):
        from app.services.audit_service import log_action
        from app.models.user import AppUser, AppRole

        # Create mock DB session
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        mock_user = AppUser(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role=AppRole.admin,
            hashed_password="hashed",
        )

        result = log_action(
            db=mock_db,
            actor=mock_user,
            action="TEST_ACTION",
            success="success",
            details={"key": "value"},
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # The added object should be an AuditLog
        added_obj = mock_db.add.call_args[0][0]
        from app.models.audit import AuditLog
        assert isinstance(added_obj, AuditLog)
        assert added_obj.actor_username == "testuser"
        assert added_obj.action == "TEST_ACTION"
        assert added_obj.success == "success"
        assert added_obj.details == {"key": "value"}

    def test_log_action_with_full_context(self):
        from app.services.audit_service import log_action
        from app.models.user import AppUser, AppRole
        from app.models.audit import AuditLog

        mock_db = MagicMock()
        mock_user = AppUser(
            id=2,
            username="approver1",
            email="approver@example.com",
            full_name="Approver One",
            role=AppRole.approver,
            hashed_password="hashed",
        )

        log_action(
            db=mock_db,
            actor=mock_user,
            action="APPROVE_REQUEST",
            access_request_id=10,
            target_db_host="db.example.com",
            target_db_service="PROD",
            target_pdb="HRPDB",
            before_state={"status": "pending_approval"},
            after_state={"status": "approved"},
            sql_executed="GRANT DBA TO JOHN",
            rollback_sql="REVOKE DBA FROM JOHN",
            result="Approved",
            success="success",
        )

        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, AuditLog)
        assert added_obj.access_request_id == 10
        assert added_obj.target_db_host == "db.example.com"
        assert added_obj.target_pdb == "HRPDB"
        assert added_obj.sql_executed == "GRANT DBA TO JOHN"
        assert added_obj.before_state == {"status": "pending_approval"}
        assert added_obj.after_state == {"status": "approved"}

    def test_log_action_timestamps(self):
        from app.services.audit_service import log_action
        from app.models.user import AppUser, AppRole
        from app.models.audit import AuditLog

        mock_db = MagicMock()
        mock_user = AppUser(
            id=3, username="u3", email="u3@example.com",
            full_name="U3", role=AppRole.requester, hashed_password="h",
        )

        before = datetime.utcnow()
        log_action(db=mock_db, actor=mock_user, action="ACTION", success="unknown")
        after = datetime.utcnow()

        added_obj = mock_db.add.call_args[0][0]
        assert before <= added_obj.created_at <= after


class TestAuditSchema:
    """Test the AuditLogOut Pydantic schema."""

    def test_audit_schema_from_model(self):
        from app.schemas.audit import AuditLogOut
        from app.models.audit import AuditLog

        now = datetime.utcnow()
        log = AuditLog(
            id=1,
            actor_id=1,
            actor_username="admin",
            action="LOGIN",
            success="success",
            created_at=now,
        )
        schema = AuditLogOut.model_validate(log)
        assert schema.actor_username == "admin"
        assert schema.action == "LOGIN"
        assert schema.success == "success"

    def test_audit_schema_optional_fields(self):
        from app.schemas.audit import AuditLogOut
        from app.models.audit import AuditLog

        log = AuditLog(
            id=2,
            actor_username="system",
            action="STARTUP",
            success="unknown",
            created_at=datetime.utcnow(),
        )
        schema = AuditLogOut.model_validate(log)
        assert schema.actor_id is None
        assert schema.access_request_id is None
        assert schema.sql_executed is None
