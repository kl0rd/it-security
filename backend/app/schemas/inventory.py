from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class OracleUser(BaseModel):
    username: str
    account_status: str
    lock_date: Optional[str] = None
    expiry_date: Optional[str] = None
    default_tablespace: Optional[str] = None
    temporary_tablespace: Optional[str] = None
    profile: Optional[str] = None
    authentication_type: Optional[str] = None
    created: Optional[str] = None
    last_login: Optional[str] = None
    common: Optional[str] = None
    oracle_maintained: Optional[str] = None


class OracleRole(BaseModel):
    role: str
    password_required: str
    authentication_type: Optional[str] = None
    common: Optional[str] = None
    oracle_maintained: Optional[str] = None


class OracleUserRoleGrant(BaseModel):
    grantee: str
    granted_role: str
    admin_option: str
    delegate_option: Optional[str] = None
    default_role: str
    common: Optional[str] = None
    inherited: Optional[str] = None


class OracleSystemPrivilege(BaseModel):
    grantee: str
    privilege: str
    admin_option: str
    common: Optional[str] = None
    inherited: Optional[str] = None


class OracleObjectPrivilege(BaseModel):
    grantee: str
    owner: str
    table_name: str
    grantor: str
    privilege: str
    grantable: str
    hierarchy: Optional[str] = None
    common: Optional[str] = None
    inherited: Optional[str] = None
    type: Optional[str] = None


class OracleProfile(BaseModel):
    profile: str
    resource_name: str
    resource_type: str
    limit: str
    common: Optional[str] = None
    inherited: Optional[str] = None


class OraclePDB(BaseModel):
    name: str
    open_mode: str
    restricted: Optional[str] = None
    con_id: Optional[int] = None


class OracleInventorySummary(BaseModel):
    host: str
    port: int
    service_name: str
    is_cdb: bool
    pdbs: List[OraclePDB] = []
    user_count: int
    role_count: int
    sys_priv_count: int
    obj_priv_count: int
    profile_count: int


class DatabaseConnectionTest(BaseModel):
    host: str
    port: int = 1521
    service_name: str
    pdb: Optional[str] = None
