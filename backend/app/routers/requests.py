from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import AppUser
from app.models.request import AccessRequest, RequestStatus
from app.schemas.request import AccessRequestCreate, AccessRequestUpdate, AccessRequestOut, GeneratedSQL
from app.services.sql_generator import generate_sql
from app.services.audit_service import log_action

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=List[AccessRequestOut])
def list_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    q = db.query(AccessRequest)
    # Requesters see only their own; approvers/admins see all
    from app.core.rbac import has_permission
    if not has_permission(current_user.role, "approve_request"):
        q = q.filter(AccessRequest.requester_id == current_user.id)
    if status_filter:
        try:
            q = q.filter(AccessRequest.status == RequestStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    return q.order_by(AccessRequest.created_at.desc()).all()


@router.post("", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    data: AccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    # Pre-generate SQL at creation time so it can be reviewed before approval
    try:
        exec_sql, rollback_sql = generate_sql(data.request_type, data.parameters)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"SQL generation error: {exc}")

    req = AccessRequest(
        title=data.title,
        description=data.description,
        request_type=data.request_type,
        status=RequestStatus.draft,
        target_db_host=data.target_db_host,
        target_db_port=data.target_db_port,
        target_db_service=data.target_db_service,
        target_pdb=data.target_pdb,
        parameters=data.parameters,
        execution_sql=exec_sql,
        rollback_sql=rollback_sql,
        requester_id=current_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    log_action(
        db, current_user, "CREATE_REQUEST",
        access_request_id=req.id,
        target_db_host=req.target_db_host,
        target_db_service=req.target_pdb or req.target_db_service,
        sql_executed=exec_sql,
        rollback_sql=rollback_sql,
        success="success",
        details={"request_type": data.request_type, "parameters": data.parameters},
    )
    return req


@router.get("/{request_id}", response_model=AccessRequestOut)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    from app.core.rbac import has_permission
    if not has_permission(current_user.role, "approve_request") and req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to view this request")
    return req


@router.patch("/{request_id}", response_model=AccessRequestOut)
def update_request(
    request_id: int,
    data: AccessRequestUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to update this request")
    if req.status not in (RequestStatus.draft, RequestStatus.rejected):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot edit a request in '{req.status}' status. Only draft/rejected requests can be edited."
        )
    if data.title is not None:
        req.title = data.title
    if data.description is not None:
        req.description = data.description
    if data.parameters is not None:
        try:
            exec_sql, rollback_sql = generate_sql(req.request_type, data.parameters)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=f"SQL generation error: {exc}")
        req.parameters = data.parameters
        req.execution_sql = exec_sql
        req.rollback_sql = rollback_sql
    db.commit()
    db.refresh(req)
    return req


@router.post("/{request_id}/submit", response_model=AccessRequestOut)
def submit_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorised to submit this request")
    if req.status != RequestStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft requests can be submitted for approval")
    req.status = RequestStatus.pending_approval
    db.commit()
    db.refresh(req)
    log_action(
        db, current_user, "SUBMIT_REQUEST",
        access_request_id=req.id,
        success="success",
    )
    return req


@router.get("/{request_id}/sql", response_model=GeneratedSQL)
def get_generated_sql(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("create_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return GeneratedSQL(
        execution_sql=req.execution_sql or "",
        rollback_sql=req.rollback_sql or "",
    )
