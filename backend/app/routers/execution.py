from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import AppUser
from app.models.request import AccessRequest, RequestStatus
from app.schemas.request import AccessRequestOut
from app.services import oracle_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/{request_id}/execute", response_model=AccessRequestOut)
def execute_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("execute_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.approved:
        raise HTTPException(
            status_code=400,
            detail=f"Only approved requests can be executed (current status: {req.status})"
        )
    if not req.execution_sql:
        raise HTTPException(status_code=400, detail="No execution SQL found on this request")

    # Execute against Oracle
    target_service = req.target_pdb or req.target_db_service
    result = oracle_service.execute_sql(
        req.target_db_host,
        req.target_db_port,
        target_service,
        req.execution_sql,
    )

    req.executor_id = current_user.id
    req.executed_at = datetime.utcnow()
    req.execution_output = result.get("output")
    req.execution_error = result.get("error")
    req.status = RequestStatus.executed if result["success"] else RequestStatus.failed

    db.commit()
    db.refresh(req)

    log_action(
        db, current_user, "EXECUTE_REQUEST",
        access_request_id=req.id,
        target_db_host=req.target_db_host,
        target_db_service=target_service,
        target_pdb=req.target_pdb,
        sql_executed=req.execution_sql,
        rollback_sql=req.rollback_sql,
        result=result.get("output") or result.get("error"),
        success="success" if result["success"] else "failure",
    )
    return req


@router.post("/{request_id}/rollback", response_model=AccessRequestOut)
def rollback_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("execute_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in (RequestStatus.executed, RequestStatus.failed):
        raise HTTPException(
            status_code=400,
            detail="Only executed or failed requests can be rolled back"
        )
    if not req.rollback_sql or req.rollback_sql.startswith("--"):
        raise HTTPException(
            status_code=400,
            detail="No automatic rollback SQL available for this request. Manual restore required."
        )

    target_service = req.target_pdb or req.target_db_service
    result = oracle_service.execute_sql(
        req.target_db_host,
        req.target_db_port,
        target_service,
        req.rollback_sql,
    )

    req.execution_output = (req.execution_output or "") + "\n[ROLLBACK] " + (
        result.get("output") or result.get("error") or ""
    )
    req.status = RequestStatus.rolled_back if result["success"] else RequestStatus.failed
    db.commit()
    db.refresh(req)

    log_action(
        db, current_user, "ROLLBACK_REQUEST",
        access_request_id=req.id,
        target_db_host=req.target_db_host,
        target_db_service=target_service,
        target_pdb=req.target_pdb,
        sql_executed=req.rollback_sql,
        result=result.get("output") or result.get("error"),
        success="success" if result["success"] else "failure",
    )
    return req
