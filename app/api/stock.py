from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import StockMovement, Material, Project, User
from app.database import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/stock", tags=["Stock Management"])

# Schemas
class StockMovementCreate(BaseModel):
    material_id: int
    movement_type: str  # IN or OUT
    quantity: float
    price_net: Optional[float] = None
    project_id: Optional[int] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    id: int
    material_id: int
    material_name: Optional[str] = None  # Added for display
    movement_type: str
    quantity: float
    price_net: Optional[float]
    project_id: Optional[int]
    project_name: Optional[str] = None  # Added for display
    invoice_number: Optional[str]
    notes: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Endpoints
@router.post("/movement", response_model=StockMovementResponse, status_code=201)
def create_stock_movement(
    movement_data: StockMovementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a stock movement (IN or OUT)"""
    # Verify material exists
    material = session.get(Material, movement_data.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Verify project exists if provided
    if movement_data.project_id:
        project = session.get(Project, movement_data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate movement type
    if movement_data.movement_type not in ["IN", "OUT"]:
        raise HTTPException(status_code=400, detail="Movement type must be IN or OUT")
    
    # Check if there's enough stock for OUT movements
    if movement_data.movement_type == "OUT":
        if material.current_stock < movement_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {material.current_stock}, requested: {movement_data.quantity}"
            )
    
    # Create stock movement
    db_movement = StockMovement(
        **movement_data.dict(),
        created_by=current_user.id
    )
    session.add(db_movement)
    
    # Update material stock
    if movement_data.movement_type == "IN":
        material.current_stock += movement_data.quantity
    else:  # OUT
        material.current_stock -= movement_data.quantity
    
    session.add(material)
    session.commit()
    session.refresh(db_movement)
    
    return db_movement

@router.get("/movements", response_model=List[StockMovementResponse])
def get_stock_movements(
    material_id: Optional[int] = None,
    project_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get stock movements with optional filters"""
    query = select(StockMovement)
    
    if material_id:
        query = query.where(StockMovement.material_id == material_id)
    if project_id:
        query = query.where(StockMovement.project_id == project_id)
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
    
    movements = session.exec(
        query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit)
    ).all()
    
    # Enrich movements with material and project names
    result = []
    for movement in movements:
        movement_dict = movement.dict()
        
        # Add material name
        material = session.get(Material, movement.material_id)
        if material:
            movement_dict['material_name'] = material.name
        
        # Add project name if project_id exists
        if movement.project_id:
            project = session.get(Project, movement.project_id)
            if project:
                movement_dict['project_name'] = project.name
        
        result.append(StockMovementResponse(**movement_dict))
    
    return result

@router.get("/movements/{movement_id}", response_model=StockMovementResponse)
def get_stock_movement(
    movement_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get stock movement by ID"""
    movement = session.get(StockMovement, movement_id)
    if not movement:
        raise HTTPException(status_code=404, detail="Stock movement not found")
    
    # Enrich with material and project names
    movement_dict = movement.dict()
    
    # Add material name
    material = session.get(Material, movement.material_id)
    if material:
        movement_dict['material_name'] = material.name
    
    # Add project name if project_id exists
    if movement.project_id:
        project = session.get(Project, movement.project_id)
        if project:
            movement_dict['project_name'] = project.name
    
    return StockMovementResponse(**movement_dict)
