from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import LaborCost, ExtraCost, Project, User
from app.database import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/costs", tags=["Costs"])

# Schemas
class LaborCostCreate(BaseModel):
    project_id: int
    description: str
    hours: float
    hourly_rate: float
    worker_name: str

class LaborCostResponse(BaseModel):
    id: int
    project_id: int
    description: str
    hours: float
    hourly_rate: float
    worker_name: str
    date: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ExtraCostCreate(BaseModel):
    project_id: int
    description: str
    amount: float
    category: str

class ExtraCostResponse(BaseModel):
    id: int
    project_id: int
    description: str
    amount: float
    category: str
    date: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Labor Cost Endpoints
@router.post("/labor", response_model=LaborCostResponse, status_code=201)
def create_labor_cost(
    cost_data: LaborCostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create labor cost entry"""
    # Verify project exists
    project = session.get(Project, cost_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_cost = LaborCost(**cost_data.dict())
    session.add(db_cost)
    session.commit()
    session.refresh(db_cost)
    return db_cost

@router.get("/labor", response_model=List[LaborCostResponse])
def get_labor_costs(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get labor costs, optionally filter by project"""
    query = select(LaborCost)
    if project_id:
        query = query.where(LaborCost.project_id == project_id)
    
    costs = session.exec(query.order_by(LaborCost.date.desc()).offset(skip).limit(limit)).all()
    return costs

@router.put("/labor/{cost_id}", response_model=LaborCostResponse)
def update_labor_cost(
    cost_id: int,
    cost_data: LaborCostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update labor cost"""
    cost = session.get(LaborCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Labor cost not found")
    
    # Verify project exists
    project = session.get(Project, cost_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in cost_data.dict().items():
        setattr(cost, key, value)
    
    session.add(cost)
    session.commit()
    session.refresh(cost)
    return cost

@router.delete("/labor/{cost_id}")
def delete_labor_cost(
    cost_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete labor cost"""
    cost = session.get(LaborCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Labor cost not found")
    
    session.delete(cost)
    session.commit()
    return {"message": "Labor cost deleted successfully"}

# Extra Cost Endpoints
@router.post("/extra", response_model=ExtraCostResponse, status_code=201)
def create_extra_cost(
    cost_data: ExtraCostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create extra cost entry"""
    # Verify project exists
    project = session.get(Project, cost_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_cost = ExtraCost(**cost_data.dict())
    session.add(db_cost)
    session.commit()
    session.refresh(db_cost)
    return db_cost

@router.get("/extra", response_model=List[ExtraCostResponse])
def get_extra_costs(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get extra costs, optionally filter by project"""
    query = select(ExtraCost)
    if project_id:
        query = query.where(ExtraCost.project_id == project_id)
    
    costs = session.exec(query.order_by(ExtraCost.date.desc()).offset(skip).limit(limit)).all()
    return costs

@router.put("/extra/{cost_id}", response_model=ExtraCostResponse)
def update_extra_cost(
    cost_id: int,
    cost_data: ExtraCostCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update extra cost"""
    cost = session.get(ExtraCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Extra cost not found")
    
    # Verify project exists
    project = session.get(Project, cost_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in cost_data.dict().items():
        setattr(cost, key, value)
    
    session.add(cost)
    session.commit()
    session.refresh(cost)
    return cost

@router.delete("/extra/{cost_id}")
def delete_extra_cost(
    cost_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete extra cost"""
    cost = session.get(ExtraCost, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Extra cost not found")
    
    session.delete(cost)
    session.commit()
    return {"message": "Extra cost deleted successfully"}
