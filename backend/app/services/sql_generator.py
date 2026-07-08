"""
Oracle SQL generator for Access Governance requests.

Each public function returns a tuple: (execution_sql, rollback_sql).
Only a fixed, well-known set of DDL/DCL statements is generated.
Free-form SQL execution is explicitly NOT supported.
"""
from typing import Any, Dict, Optional, Tuple
from app.models.request import RequestType


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_sql(request_type: RequestType, parameters: Dict[str, Any]) -> Tuple[str, str]:
    """Generate (execution_sql, rollback_sql) for the given request type."""
    generators = {
        RequestType.create_user: _create_user,
        RequestType.drop_user: _drop_user,
        RequestType.lock_user: _lock_user,
        RequestType.unlock_user: _unlock_user,
        RequestType.grant_role: _grant_role,
        RequestType.revoke_role: _revoke_role,
        RequestType.grant_system_privilege: _grant_system_privilege,
        RequestType.revoke_system_privilege: _revoke_system_privilege,
        RequestType.grant_object_privilege: _grant_object_privilege,
        RequestType.revoke_object_privilege: _revoke_object_privilege,
    }
    fn = generators.get(request_type)
    if fn is None:
        raise ValueError(f"Unsupported request type: {request_type}")
    return fn(parameters)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_identifier(name: str, field: str = "identifier") -> str:
    """Ensure an Oracle identifier contains only safe characters."""
    import re
    if not name:
        raise ValueError(f"{field} must not be empty")
    if not re.match(r'^[A-Za-z][A-Za-z0-9_$#]{0,127}$', name):
        raise ValueError(
            f"Invalid Oracle {field}: '{name}'. "
            "Must start with a letter and contain only letters, digits, _, $, #."
        )
    return name.upper()


def _validate_schema_object(owner: str, obj: str) -> Tuple[str, str]:
    """Validate and return (owner_upper, object_upper)."""
    return _validate_identifier(owner, "owner"), _validate_identifier(obj, "object_name")


VALID_SYSTEM_PRIVILEGES = frozenset({
    "CREATE SESSION", "CREATE TABLE", "CREATE VIEW", "CREATE SEQUENCE",
    "CREATE PROCEDURE", "CREATE TRIGGER", "CREATE TYPE", "CREATE SYNONYM",
    "CREATE INDEX", "CREATE CLUSTER", "CREATE DATABASE LINK",
    "CREATE PUBLIC SYNONYM", "CREATE PUBLIC DATABASE LINK",
    "ALTER SESSION", "ALTER USER", "ALTER TABLE", "ALTER ANY TABLE",
    "DROP ANY TABLE", "DROP USER", "DROP ANY VIEW", "DROP ANY PROCEDURE",
    "SELECT ANY TABLE", "SELECT ANY DICTIONARY", "INSERT ANY TABLE",
    "UPDATE ANY TABLE", "DELETE ANY TABLE", "EXECUTE ANY PROCEDURE",
    "GRANT ANY PRIVILEGE", "GRANT ANY ROLE", "GRANT ANY OBJECT PRIVILEGE",
    "CONNECT", "RESOURCE", "DBA", "SYSDBA", "SYSOPER",
    "CREATE ANY TABLE", "CREATE ANY VIEW", "CREATE ANY PROCEDURE",
    "CREATE ANY SEQUENCE", "CREATE ANY TRIGGER", "CREATE ANY INDEX",
    "UNLIMITED TABLESPACE", "MANAGE TABLESPACE",
})

VALID_OBJECT_PRIVILEGES = frozenset({
    "SELECT", "INSERT", "UPDATE", "DELETE", "EXECUTE", "REFERENCES",
    "ALTER", "INDEX", "ALL PRIVILEGES", "FLASHBACK", "ON COMMIT REFRESH",
    "QUERY REWRITE", "DEBUG", "UNDER",
})


def _validate_system_privilege(priv: str) -> str:
    up = priv.upper().strip()
    if up not in VALID_SYSTEM_PRIVILEGES:
        raise ValueError(f"Unrecognised system privilege: '{priv}'")
    return up


def _validate_object_privilege(priv: str) -> str:
    up = priv.upper().strip()
    if up not in VALID_OBJECT_PRIVILEGES:
        raise ValueError(f"Unrecognised object privilege: '{priv}'")
    return up


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def _create_user(params: Dict[str, Any]) -> Tuple[str, str]:
    username = _validate_identifier(params["username"], "username")
    profile = _validate_identifier(params.get("profile", "DEFAULT"), "profile")
    default_ts = _validate_identifier(params.get("default_tablespace", "USERS"), "default_tablespace")
    temp_ts = _validate_identifier(params.get("temporary_tablespace", "TEMP"), "temporary_tablespace")

    exec_sql = (
        f'CREATE USER {username}\n'
        f'  IDENTIFIED EXTERNALLY\n'
        f'  DEFAULT TABLESPACE {default_ts}\n'
        f'  TEMPORARY TABLESPACE {temp_ts}\n'
        f'  PROFILE {profile}\n'
        f'  ACCOUNT UNLOCK'
    )
    rollback_sql = f'DROP USER {username} CASCADE'
    return exec_sql, rollback_sql


def _drop_user(params: Dict[str, Any]) -> Tuple[str, str]:
    username = _validate_identifier(params["username"], "username")
    cascade = params.get("cascade", True)
    cascade_clause = " CASCADE" if cascade else ""

    exec_sql = f'DROP USER {username}{cascade_clause}'
    # Rollback: recreating a dropped user is not fully reversible without a backup.
    # We document this as a manual restore step.
    rollback_sql = (
        f'-- Manual rollback required: recreate user {username} from a database backup\n'
        f'-- CREATE USER {username} IDENTIFIED EXTERNALLY'
    )
    return exec_sql, rollback_sql


def _lock_user(params: Dict[str, Any]) -> Tuple[str, str]:
    username = _validate_identifier(params["username"], "username")
    exec_sql = f'ALTER USER {username} ACCOUNT LOCK'
    rollback_sql = f'ALTER USER {username} ACCOUNT UNLOCK'
    return exec_sql, rollback_sql


def _unlock_user(params: Dict[str, Any]) -> Tuple[str, str]:
    username = _validate_identifier(params["username"], "username")
    exec_sql = f'ALTER USER {username} ACCOUNT UNLOCK'
    rollback_sql = f'ALTER USER {username} ACCOUNT LOCK'
    return exec_sql, rollback_sql


def _grant_role(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    role = _validate_identifier(params["role"], "role")
    admin_option = bool(params.get("admin_option", False))

    with_clause = " WITH ADMIN OPTION" if admin_option else ""
    exec_sql = f'GRANT {role} TO {grantee}{with_clause}'
    rollback_sql = f'REVOKE {role} FROM {grantee}'
    return exec_sql, rollback_sql


def _revoke_role(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    role = _validate_identifier(params["role"], "role")

    exec_sql = f'REVOKE {role} FROM {grantee}'
    rollback_sql = f'GRANT {role} TO {grantee}'
    return exec_sql, rollback_sql


def _grant_system_privilege(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    privilege = _validate_system_privilege(params["privilege"])
    admin_option = bool(params.get("admin_option", False))

    with_clause = " WITH ADMIN OPTION" if admin_option else ""
    exec_sql = f'GRANT {privilege} TO {grantee}{with_clause}'
    rollback_sql = f'REVOKE {privilege} FROM {grantee}'
    return exec_sql, rollback_sql


def _revoke_system_privilege(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    privilege = _validate_system_privilege(params["privilege"])

    exec_sql = f'REVOKE {privilege} FROM {grantee}'
    rollback_sql = f'GRANT {privilege} TO {grantee}'
    return exec_sql, rollback_sql


def _grant_object_privilege(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    privilege = _validate_object_privilege(params["privilege"])
    owner, obj = _validate_schema_object(params["object_owner"], params["object_name"])
    grant_option = bool(params.get("grant_option", False))
    columns: Optional[list] = params.get("columns")

    col_clause = ""
    if columns:
        validated_cols = [_validate_identifier(c, "column") for c in columns]
        col_clause = f" ({', '.join(validated_cols)})"

    with_clause = " WITH GRANT OPTION" if grant_option else ""
    exec_sql = f'GRANT {privilege}{col_clause} ON {owner}.{obj} TO {grantee}{with_clause}'
    rollback_sql = f'REVOKE {privilege}{col_clause} ON {owner}.{obj} FROM {grantee}'
    return exec_sql, rollback_sql


def _revoke_object_privilege(params: Dict[str, Any]) -> Tuple[str, str]:
    grantee = _validate_identifier(params["grantee"], "grantee")
    privilege = _validate_object_privilege(params["privilege"])
    owner, obj = _validate_schema_object(params["object_owner"], params["object_name"])
    columns: Optional[list] = params.get("columns")

    col_clause = ""
    if columns:
        validated_cols = [_validate_identifier(c, "column") for c in columns]
        col_clause = f" ({', '.join(validated_cols)})"

    exec_sql = f'REVOKE {privilege}{col_clause} ON {owner}.{obj} FROM {grantee}'
    rollback_sql = f'GRANT {privilege}{col_clause} ON {owner}.{obj} TO {grantee}'
    return exec_sql, rollback_sql
