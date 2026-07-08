from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import AppUser
from app.models.request import AccessRequest, RequestStatus
from app.schemas.request import AccessRequestOut, ApproveRequest
from app.services.audit_service import log_action

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=List[AccessRequestOut])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("approve_request")),
):
    return (
        db.query(AccessRequest)
        .filter(AccessRequest.status == RequestStatus.pending_approval)
        .order_by(AccessRequest.created_at.asc())
        .all()
    )


@router.post("/{request_id}", response_model=AccessRequestOut)
def approve_or_reject_request(
    request_id: int,
    payload: ApproveRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("approve_request")),
):
    req = db.query(AccessRequest).filter(AccessRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.pending_approval:
        raise HTTPException(
            status_code=400,
            detail=f"Request is not pending approval (current status: {req.status})"
        )
    # Approver cannot approve their own request
    if req.requester_id == current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot approve your own request"
        )

    if payload.approved:
        req.status = RequestStatus.approved
        req.approver_id = current_user.id
        req.approved_at = datetime.utcnow()
        action = "APPROVE_REQUEST"
    else:
        if not payload.rejection_reason:
            raise HTTPException(status_code=400, detail="rejection_reason is required when rejecting")
        req.status = RequestStatus.rejected
        req.approver_id = current_user.id
        req.rejection_reason = payload.rejection_reason
        action = "REJECT_REQUEST"

    db.commit()
    db.refresh(req)
    log_action(
        db, current_user, action,
        access_request_id=req.id,
        target_db_host=req.target_db_host,
        target_db_service=req.target_pdb or req.target_db_service,
        success="success",
        details={"approved": payload.approved, "rejection_reason": payload.rejection_reason},
    )
    return req
