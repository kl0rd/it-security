"""
Oracle database service: connects to Oracle and reads inventory data.

Passwords are supplied via environment variables only; they are never stored
in the application database.
"""
from typing import Any, Dict, List, Optional
import logging

from app.config import get_settings
from app.schemas.inventory import (
    OracleUser, OracleRole, OracleUserRoleGrant, OracleSystemPrivilege,
    OracleObjectPrivilege, OracleProfile, OraclePDB,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    service_name: Optional[str] = None,
    pdb: Optional[str] = None,
):
    """Return an oracledb connection using the privileged service account.

    The password is read from environment variables only.
    Raises RuntimeError if oracledb is not available or connection fails.
    """
    try:
        import oracledb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("oracledb package is not installed") from exc

    h = host or settings.ORACLE_HOST
    p = port or settings.ORACLE_PORT
    sn = pdb or service_name or settings.ORACLE_SERVICE_NAME

    password = settings.ORACLE_ADMIN_PASSWORD
    if not password:
        raise RuntimeError(
            "ORACLE_ADMIN_PASSWORD environment variable is not set. "
            "Set it before connecting to Oracle."
        )

    dsn = oracledb.makedsn(h, p, service_name=sn)
    return oracledb.connect(user=settings.ORACLE_ADMIN_USER, password=password, dsn=dsn)


def _row_to_dict(cursor, row) -> Dict[str, Any]:
    return {desc[0].lower(): val for desc, val in zip(cursor.description, row)}


def test_connection(host: str, port: int, service_name: str, pdb: Optional[str] = None) -> bool:
    """Test connectivity to an Oracle database."""
    try:
        conn = _get_connection(host, port, service_name, pdb)
        conn.close()
        return True
    except Exception as exc:
        logger.warning("Oracle connection test failed: %s", exc)
        return False


def is_cdb(host: str, port: int, service_name: str) -> bool:
    """Return True if the database is a Container Database."""
    try:
        conn = _get_connection(host, port, service_name)
        with conn.cursor() as cur:
            cur.execute("SELECT CDB FROM V$DATABASE")
            row = cur.fetchone()
        conn.close()
        return bool(row and row[0] == "YES")
    except Exception as exc:
        logger.warning("Could not determine CDB status: %s", exc)
        return False


def list_pdbs(host: str, port: int, service_name: str) -> List[OraclePDB]:
    """List pluggable databases (only meaningful on a CDB)."""
    try:
        conn = _get_connection(host, port, service_name)
        with conn.cursor() as cur:
            cur.execute("SELECT NAME, OPEN_MODE, RESTRICTED, CON_ID FROM V$PDBS ORDER BY NAME")
            rows = cur.fetchall()
        conn.close()
        return [
            OraclePDB(
                name=r[0],
                open_mode=r[1] or "",
                restricted=r[2],
                con_id=r[3],
            )
            for r in rows
        ]
    except Exception as exc:
        logger.warning("Could not list PDBs: %s", exc)
        return []


def get_users(host: str, port: int, service_name: str) -> List[OracleUser]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    USERNAME,
                    ACCOUNT_STATUS,
                    TO_CHAR(LOCK_DATE, 'YYYY-MM-DD HH24:MI:SS') AS LOCK_DATE,
                    TO_CHAR(EXPIRY_DATE, 'YYYY-MM-DD HH24:MI:SS') AS EXPIRY_DATE,
                    DEFAULT_TABLESPACE,
                    TEMPORARY_TABLESPACE,
                    PROFILE,
                    AUTHENTICATION_TYPE,
                    TO_CHAR(CREATED, 'YYYY-MM-DD HH24:MI:SS') AS CREATED,
                    TO_CHAR(LAST_LOGIN, 'YYYY-MM-DD HH24:MI:SS') AS LAST_LOGIN,
                    COMMON,
                    ORACLE_MAINTAINED
                FROM DBA_USERS
                ORDER BY USERNAME
            """)
            rows = cur.fetchall()
        return [
            OracleUser(
                username=r[0],
                account_status=r[1],
                lock_date=r[2],
                expiry_date=r[3],
                default_tablespace=r[4],
                temporary_tablespace=r[5],
                profile=r[6],
                authentication_type=r[7],
                created=r[8],
                last_login=r[9],
                common=r[10],
                oracle_maintained=r[11],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_roles(host: str, port: int, service_name: str) -> List[OracleRole]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ROLE, PASSWORD_REQUIRED, AUTHENTICATION_TYPE, COMMON, ORACLE_MAINTAINED
                FROM DBA_ROLES
                ORDER BY ROLE
            """)
            rows = cur.fetchall()
        return [
            OracleRole(
                role=r[0],
                password_required=r[1],
                authentication_type=r[2],
                common=r[3],
                oracle_maintained=r[4],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_role_privs(host: str, port: int, service_name: str) -> List[OracleUserRoleGrant]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GRANTEE, GRANTED_ROLE, ADMIN_OPTION, DELEGATE_OPTION, DEFAULT_ROLE, COMMON, INHERITED
                FROM DBA_ROLE_PRIVS
                ORDER BY GRANTEE, GRANTED_ROLE
            """)
            rows = cur.fetchall()
        return [
            OracleUserRoleGrant(
                grantee=r[0],
                granted_role=r[1],
                admin_option=r[2],
                delegate_option=r[3],
                default_role=r[4],
                common=r[5],
                inherited=r[6],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_sys_privs(host: str, port: int, service_name: str) -> List[OracleSystemPrivilege]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GRANTEE, PRIVILEGE, ADMIN_OPTION, COMMON, INHERITED
                FROM DBA_SYS_PRIVS
                ORDER BY GRANTEE, PRIVILEGE
            """)
            rows = cur.fetchall()
        return [
            OracleSystemPrivilege(
                grantee=r[0],
                privilege=r[1],
                admin_option=r[2],
                common=r[3],
                inherited=r[4],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_tab_privs(host: str, port: int, service_name: str) -> List[OracleObjectPrivilege]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GRANTEE, OWNER, TABLE_NAME, GRANTOR, PRIVILEGE, GRANTABLE, HIERARCHY, COMMON, INHERITED, TYPE
                FROM DBA_TAB_PRIVS
                ORDER BY GRANTEE, OWNER, TABLE_NAME
            """)
            rows = cur.fetchall()
        return [
            OracleObjectPrivilege(
                grantee=r[0],
                owner=r[1],
                table_name=r[2],
                grantor=r[3],
                privilege=r[4],
                grantable=r[5],
                hierarchy=r[6],
                common=r[7],
                inherited=r[8],
                type=r[9],
            )
            for r in rows
        ]
    finally:
        conn.close()


def get_profiles(host: str, port: int, service_name: str) -> List[OracleProfile]:
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT PROFILE, RESOURCE_NAME, RESOURCE_TYPE, LIMIT, COMMON, INHERITED
                FROM DBA_PROFILES
                ORDER BY PROFILE, RESOURCE_NAME
            """)
            rows = cur.fetchall()
        return [
            OracleProfile(
                profile=r[0],
                resource_name=r[1],
                resource_type=r[2],
                limit=r[3] or "DEFAULT",
                common=r[4],
                inherited=r[5],
            )
            for r in rows
        ]
    finally:
        conn.close()


def execute_sql(
    host: str,
    port: int,
    service_name: str,
    sql: str,
) -> Dict[str, Any]:
    """
    Execute a single pre-generated, pre-approved SQL statement against Oracle.
    Returns a dict with 'success', 'output', 'error' keys.

    NOTE: This function must only be called with SQL generated by sql_generator.py
    after it has been approved through the workflow. Free-form SQL is NOT accepted.
    """
    conn = _get_connection(host, port, service_name)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        return {"success": True, "output": "Statement executed successfully.", "error": None}
    except Exception as exc:
        conn.rollback()
        return {"success": False, "output": None, "error": str(exc)}
    finally:
        conn.close()
