"""Initial schema: app_users, access_requests, audit_logs

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # app_users
    op.create_table(
        "app_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "approver", "requester", "auditor", name="approle"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_app_users_id"), "app_users", ["id"], unique=False)
    op.create_index(op.f("ix_app_users_username"), "app_users", ["username"], unique=True)
    op.create_index(op.f("ix_app_users_email"), "app_users", ["email"], unique=True)

    # access_requests
    op.create_table(
        "access_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "request_type",
            sa.Enum(
                "create_user", "drop_user", "lock_user", "unlock_user",
                "grant_role", "revoke_role", "grant_system_privilege",
                "revoke_system_privilege", "grant_object_privilege",
                "revoke_object_privilege",
                name="requesttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "pending_approval", "approved", "rejected",
                "executed", "failed", "rolled_back",
                name="requeststatus",
            ),
            nullable=False,
        ),
        sa.Column("target_db_host", sa.String(length=255), nullable=False),
        sa.Column("target_db_port", sa.Integer(), nullable=False),
        sa.Column("target_db_service", sa.String(length=255), nullable=False),
        sa.Column("target_pdb", sa.String(length=255), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("execution_sql", sa.Text(), nullable=True),
        sa.Column("rollback_sql", sa.Text(), nullable=True),
        sa.Column("execution_output", sa.Text(), nullable=True),
        sa.Column("execution_error", sa.Text(), nullable=True),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("executor_id", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["approver_id"], ["app_users.id"]),
        sa.ForeignKeyConstraint(["executor_id"], ["app_users.id"]),
        sa.ForeignKeyConstraint(["requester_id"], ["app_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_access_requests_id"), "access_requests", ["id"], unique=False)

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_username", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("access_request_id", sa.Integer(), nullable=True),
        sa.Column("target_db_host", sa.String(length=255), nullable=True),
        sa.Column("target_db_service", sa.String(length=255), nullable=True),
        sa.Column("target_pdb", sa.String(length=255), nullable=True),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("sql_executed", sa.Text(), nullable=True),
        sa.Column("rollback_sql", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("success", sa.String(length=8), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["access_request_id"], ["access_requests.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["app_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_access_requests_id"), table_name="access_requests")
    op.drop_table("access_requests")
    op.drop_index(op.f("ix_app_users_email"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_username"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_id"), table_name="app_users")
    op.drop_table("app_users")
    op.execute("DROP TYPE IF EXISTS approle")
    op.execute("DROP TYPE IF EXISTS requesttype")
    op.execute("DROP TYPE IF EXISTS requeststatus")
