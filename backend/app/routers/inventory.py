from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import AppUser
from app.schemas.inventory import (
    OracleUser, OracleRole, OracleUserRoleGrant, OracleSystemPrivilege,
    OracleObjectPrivilege, OracleProfile, OraclePDB, OracleInventorySummary,
    DatabaseConnectionTest,
)
from app.services import oracle_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _resolve(
    host: str,
    port: int,
    service_name: str,
    pdb: Optional[str],
    db: Session,
    current_user: AppUser,
):
    """Common helper that logs the inventory query."""
    log_action(
        db, current_user, "VIEW_INVENTORY",
        target_db_host=host, target_db_service=pdb or service_name, target_pdb=pdb,
        success="success",
    )
    effective_service = pdb if pdb else service_name
    return host, port, effective_service


@router.post("/test-connection")
def test_connection(
    payload: DatabaseConnectionTest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    result = oracle_service.test_connection(
        payload.host, payload.port, payload.service_name, payload.pdb
    )
    return {"connected": result}


@router.get("/summary", response_model=OracleInventorySummary)
def get_summary(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    cdb = oracle_service.is_cdb(h, p, sn)
    pdbs = oracle_service.list_pdbs(h, p, sn) if cdb else []
    users = oracle_service.get_users(h, p, sn)
    roles = oracle_service.get_roles(h, p, sn)
    sys_privs = oracle_service.get_sys_privs(h, p, sn)
    obj_privs = oracle_service.get_tab_privs(h, p, sn)
    profiles = oracle_service.get_profiles(h, p, sn)
    return OracleInventorySummary(
        host=h, port=p, service_name=sn,
        is_cdb=cdb, pdbs=pdbs,
        user_count=len(users), role_count=len(roles),
        sys_priv_count=len(sys_privs), obj_priv_count=len(obj_privs),
        profile_count=len(profiles),
    )


@router.get("/users", response_model=List[OracleUser])
def list_oracle_users(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_users(h, p, sn)


@router.get("/roles", response_model=List[OracleRole])
def list_oracle_roles(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_roles(h, p, sn)


@router.get("/role-privs", response_model=List[OracleUserRoleGrant])
def list_role_privs(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_role_privs(h, p, sn)


@router.get("/sys-privs", response_model=List[OracleSystemPrivilege])
def list_sys_privs(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_sys_privs(h, p, sn)


@router.get("/tab-privs", response_model=List[OracleObjectPrivilege])
def list_tab_privs(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_tab_privs(h, p, sn)


@router.get("/profiles", response_model=List[OracleProfile])
def list_profiles(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    pdb: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    h, p, sn = _resolve(host, port, service_name, pdb, db, current_user)
    return oracle_service.get_profiles(h, p, sn)


@router.get("/pdbs", response_model=List[OraclePDB])
def list_pdbs(
    host: str = Query(...),
    port: int = Query(1521),
    service_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("view_inventory")),
):
    return oracle_service.list_pdbs(host, port, service_name)
