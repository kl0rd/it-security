"""Unit tests for the Oracle SQL generator.

These tests do NOT require a real Oracle database connection.
They validate that the correct SQL is produced for each request type
and that invalid inputs are rejected.
"""
import pytest
from app.services.sql_generator import generate_sql, _validate_identifier
from app.models.request import RequestType


class TestCreateUser:
    def test_basic_create_user(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.create_user,
            {"username": "john_doe", "profile": "DEFAULT", "default_tablespace": "USERS", "temporary_tablespace": "TEMP"},
        )
        assert "CREATE USER JOHN_DOE" in exec_sql
        assert "IDENTIFIED EXTERNALLY" in exec_sql
        assert "DEFAULT TABLESPACE USERS" in exec_sql
        assert "PROFILE DEFAULT" in exec_sql
        assert rollback_sql == "DROP USER JOHN_DOE CASCADE"

    def test_create_user_defaults(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.create_user,
            {"username": "testuser"},
        )
        assert "CREATE USER TESTUSER" in exec_sql
        assert "DEFAULT TABLESPACE USERS" in exec_sql
        assert "TEMPORARY TABLESPACE TEMP" in exec_sql

    def test_create_user_invalid_name(self):
        with pytest.raises(ValueError, match="Invalid Oracle"):
            generate_sql(RequestType.create_user, {"username": "DROP TABLE users"})

    def test_create_user_sql_injection_attempt(self):
        with pytest.raises(ValueError):
            generate_sql(RequestType.create_user, {"username": "'; DROP TABLE users; --"})

    def test_create_user_empty_name(self):
        with pytest.raises(ValueError):
            generate_sql(RequestType.create_user, {"username": ""})

    def test_create_user_missing_username(self):
        with pytest.raises(KeyError):
            generate_sql(RequestType.create_user, {})


class TestDropUser:
    def test_basic_drop_user(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.drop_user,
            {"username": "john_doe", "cascade": True},
        )
        assert exec_sql == "DROP USER JOHN_DOE CASCADE"
        assert "Manual rollback required" in rollback_sql

    def test_drop_user_no_cascade(self):
        exec_sql, _ = generate_sql(
            RequestType.drop_user,
            {"username": "john_doe", "cascade": False},
        )
        assert exec_sql == "DROP USER JOHN_DOE"
        assert "CASCADE" not in exec_sql


class TestLockUnlockUser:
    def test_lock_user(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.lock_user,
            {"username": "john_doe"},
        )
        assert exec_sql == "ALTER USER JOHN_DOE ACCOUNT LOCK"
        assert rollback_sql == "ALTER USER JOHN_DOE ACCOUNT UNLOCK"

    def test_unlock_user(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.unlock_user,
            {"username": "john_doe"},
        )
        assert exec_sql == "ALTER USER JOHN_DOE ACCOUNT UNLOCK"
        assert rollback_sql == "ALTER USER JOHN_DOE ACCOUNT LOCK"

    def test_lock_unlock_symmetry(self):
        lock_exec, lock_rb = generate_sql(RequestType.lock_user, {"username": "u1"})
        unlock_exec, unlock_rb = generate_sql(RequestType.unlock_user, {"username": "u1"})
        assert lock_exec == unlock_rb
        assert unlock_exec == lock_rb


class TestGrantRevokeRole:
    def test_grant_role(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.grant_role,
            {"grantee": "john", "role": "DBA"},
        )
        assert exec_sql == "GRANT DBA TO JOHN"
        assert rollback_sql == "REVOKE DBA FROM JOHN"

    def test_grant_role_with_admin_option(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.grant_role,
            {"grantee": "john", "role": "CONNECT", "admin_option": True},
        )
        assert "WITH ADMIN OPTION" in exec_sql

    def test_revoke_role(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.revoke_role,
            {"grantee": "john", "role": "DBA"},
        )
        assert exec_sql == "REVOKE DBA FROM JOHN"
        assert rollback_sql == "GRANT DBA TO JOHN"

    def test_grant_revoke_role_symmetry(self):
        grant_exec, grant_rb = generate_sql(
            RequestType.grant_role, {"grantee": "u1", "role": "MYROLE"}
        )
        revoke_exec, revoke_rb = generate_sql(
            RequestType.revoke_role, {"grantee": "u1", "role": "MYROLE"}
        )
        assert grant_exec == revoke_rb
        assert revoke_exec == grant_rb


class TestGrantRevokeSystemPrivilege:
    def test_grant_sys_priv(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.grant_system_privilege,
            {"grantee": "john", "privilege": "CREATE SESSION"},
        )
        assert exec_sql == "GRANT CREATE SESSION TO JOHN"
        assert rollback_sql == "REVOKE CREATE SESSION FROM JOHN"

    def test_grant_sys_priv_with_admin(self):
        exec_sql, _ = generate_sql(
            RequestType.grant_system_privilege,
            {"grantee": "john", "privilege": "CREATE SESSION", "admin_option": True},
        )
        assert "WITH ADMIN OPTION" in exec_sql

    def test_revoke_sys_priv(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.revoke_system_privilege,
            {"grantee": "john", "privilege": "CREATE TABLE"},
        )
        assert exec_sql == "REVOKE CREATE TABLE FROM JOHN"
        assert rollback_sql == "GRANT CREATE TABLE TO JOHN"

    def test_invalid_system_privilege(self):
        with pytest.raises(ValueError, match="Unrecognised system privilege"):
            generate_sql(
                RequestType.grant_system_privilege,
                {"grantee": "john", "privilege": "DO EVERYTHING"},
            )

    def test_privilege_case_insensitive(self):
        exec_sql, _ = generate_sql(
            RequestType.grant_system_privilege,
            {"grantee": "john", "privilege": "create session"},
        )
        assert "CREATE SESSION" in exec_sql


class TestGrantRevokeObjectPrivilege:
    def test_grant_object_priv(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.grant_object_privilege,
            {"grantee": "john", "privilege": "SELECT", "object_owner": "hr", "object_name": "employees"},
        )
        assert exec_sql == "GRANT SELECT ON HR.EMPLOYEES TO JOHN"
        assert rollback_sql == "REVOKE SELECT ON HR.EMPLOYEES FROM JOHN"

    def test_grant_object_priv_with_grant_option(self):
        exec_sql, _ = generate_sql(
            RequestType.grant_object_privilege,
            {
                "grantee": "john", "privilege": "SELECT",
                "object_owner": "hr", "object_name": "employees",
                "grant_option": True,
            },
        )
        assert "WITH GRANT OPTION" in exec_sql

    def test_grant_object_priv_with_columns(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.grant_object_privilege,
            {
                "grantee": "john", "privilege": "UPDATE",
                "object_owner": "hr", "object_name": "employees",
                "columns": ["salary", "commission_pct"],
            },
        )
        assert "UPDATE (SALARY, COMMISSION_PCT) ON HR.EMPLOYEES TO JOHN" in exec_sql
        assert "(SALARY, COMMISSION_PCT)" in rollback_sql

    def test_revoke_object_priv(self):
        exec_sql, rollback_sql = generate_sql(
            RequestType.revoke_object_privilege,
            {"grantee": "john", "privilege": "INSERT", "object_owner": "hr", "object_name": "employees"},
        )
        assert exec_sql == "REVOKE INSERT ON HR.EMPLOYEES FROM JOHN"
        assert rollback_sql == "GRANT INSERT ON HR.EMPLOYEES TO JOHN"

    def test_invalid_object_privilege(self):
        with pytest.raises(ValueError, match="Unrecognised object privilege"):
            generate_sql(
                RequestType.grant_object_privilege,
                {"grantee": "john", "privilege": "HACK", "object_owner": "hr", "object_name": "emp"},
            )

    def test_sql_injection_in_object_name(self):
        with pytest.raises(ValueError):
            generate_sql(
                RequestType.grant_object_privilege,
                {
                    "grantee": "john",
                    "privilege": "SELECT",
                    "object_owner": "hr",
                    "object_name": "emp; DROP TABLE users",
                },
            )


class TestIdentifierValidation:
    def test_valid_identifiers(self):
        valid = ["ABC", "user1", "MY_TABLE", "T$1", "A#B"]
        for name in valid:
            result = _validate_identifier(name)
            assert result == name.upper()

    def test_invalid_identifiers(self):
        invalid = ["1start", "has space", "has-dash", "has.dot", "", "a" * 129]
        for name in invalid:
            with pytest.raises(ValueError):
                _validate_identifier(name)

    def test_uppercase_output(self):
        assert _validate_identifier("lowercase") == "LOWERCASE"


class TestUnsupportedRequestType:
    def test_raises_for_unknown_type(self):
        with pytest.raises((ValueError, AttributeError)):
            generate_sql("UNKNOWN_TYPE", {})
