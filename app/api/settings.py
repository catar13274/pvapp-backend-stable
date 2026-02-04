from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models import CompanySetting, User
from app.database import get_session
from app.auth import get_current_user, get_current_admin_user
from datetime import datetime

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Schemas
class CompanySettingCreate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class CompanySettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Endpoints
@router.get("/", response_model=List[CompanySettingResponse])
def get_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all company settings"""
    settings = session.exec(select(CompanySetting)).all()
    return settings

@router.post("/", response_model=CompanySettingResponse)
def create_or_update_setting(
    setting_data: CompanySettingCreate,
    session: Session = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create or update a company setting (Admin only)"""
    # Check if setting already exists
    existing = session.exec(
        select(CompanySetting).where(CompanySetting.key == setting_data.key)
    ).first()
    
    if existing:
        # Update existing setting
        existing.value = setting_data.value
        if setting_data.description:
            existing.description = setting_data.description
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new setting
        db_setting = CompanySetting(**setting_data.dict())
        session.add(db_setting)
        session.commit()
        session.refresh(db_setting)
        return db_setting

@router.get("/{key}", response_model=CompanySettingResponse)
def get_setting(
    key: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific setting by key"""
    setting = session.exec(
        select(CompanySetting).where(CompanySetting.key == key)
    ).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return setting

@router.delete("/{key}")
def delete_setting(
    key: str,
    session: Session = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a setting (Admin only)"""
    setting = session.exec(
        select(CompanySetting).where(CompanySetting.key == key)
    ).first()
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    session.delete(setting)
    session.commit()
    return {"message": "Setting deleted successfully"}
