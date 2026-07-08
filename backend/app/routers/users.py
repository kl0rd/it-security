from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import get_password_hash
from app.models.user import AppUser, AppRole
from app.schemas.user import AppUserCreate, AppUserUpdate, AppUserOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[AppUserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("manage_users")),
):
    return db.query(AppUser).all()


@router.post("", response_model=AppUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AppUserCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("manage_users")),
):
    existing = db.query(AppUser).filter(
        (AppUser.username == data.username) | (AppUser.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = AppUser(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        is_active=data.is_active,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(
        db, current_user, "CREATE_APP_USER",
        details={"new_user": data.username, "role": data.role},
        success="success",
    )
    return user


@router.get("/{user_id}", response_model=AppUserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("manage_users")),
):
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=AppUserOut)
def update_user(
    user_id: int,
    data: AppUserUpdate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role("manage_users")),
):
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    before = {"role": user.role, "is_active": user.is_active}
    if data.email is not None:
        user.email = data.email
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.password is not None:
        user.hashed_password = get_password_hash(data.password)
    db.commit()
    db.refresh(user)
    log_action(
        db, current_user, "UPDATE_APP_USER",
        before_state=before,
        after_state={"role": user.role, "is_active": user.is_active},
        details={"target_user": user.username},
        success="success",
    )
    return user
