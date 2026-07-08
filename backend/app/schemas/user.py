from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import AppRole


class AppUserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: AppRole = AppRole.requester
    is_active: bool = True


class AppUserCreate(AppUserBase):
    password: str


class AppUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[AppRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class AppUserOut(AppUserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
