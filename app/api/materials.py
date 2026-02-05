"""
Materials Management API
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.models import Material, StockMovement
from app.database import get_session

router = APIRouter(prefix="/materials", tags=["Materials"])

@router.get("/", response_model=List[Material])
async def list_materials(
    company_id: int,
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """List all materials for a company"""
    statement = select(Material).where(
        Material.company_id == company_id
    ).offset(skip).limit(limit)
    materials = session.exec(statement).all()
    return materials

@router.get("/{material_id}", response_model=Material)
async def get_material(material_id: int, session: Session = Depends(get_session)):
    """Get material by ID"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.post("/", response_model=Material)
async def create_material(material: Material, session: Session = Depends(get_session)):
    """Create new material"""
    session.add(material)
    session.commit()
    session.refresh(material)
    return material

@router.put("/{material_id}", response_model=Material)
async def update_material(
    material_id: int,
    material_data: Material,
    session: Session = Depends(get_session)
):
    """Update material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    material_data_dict = material_data.dict(exclude_unset=True)
    for key, value in material_data_dict.items():
        setattr(material, key, value)
    
    session.commit()
    session.refresh(material)
    return material

@router.delete("/{material_id}")
async def delete_material(material_id: int, session: Session = Depends(get_session)):
    """Delete material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    session.delete(material)
    session.commit()
    
    return {"message": "Material deleted successfully"}

@router.post("/{material_id}/stock/adjust")
async def adjust_stock(
    material_id: int,
    change: float,
    movement_type: str,
    session: Session = Depends(get_session)
):
    """Adjust material stock"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update stock
    material.current_stock += change
    
    # Create stock movement
    movement = StockMovement(
        material_id=material_id,
        company_id=material.company_id,
        change=change,
        movement_type=movement_type,
        quantity=material.current_stock
    )
    
    session.add(movement)
    session.commit()
    session.refresh(material)
    
    return {"material": material, "new_stock": material.current_stock}

@router.get("/{material_id}/movements")
async def get_material_movements(
    material_id: int,
    session: Session = Depends(get_session),
    limit: int = 50
):
    """Get stock movements for a material"""
    statement = select(StockMovement).where(
        StockMovement.material_id == material_id
    ).order_by(StockMovement.created_at.desc()).limit(limit)
    
    movements = session.exec(statement).all()
    return movements

@router.get("/company/{company_id}/low-stock")
async def get_low_stock_materials(
    company_id: int,
    session: Session = Depends(get_session)
):
    """Get materials with low stock for a company"""
    statement = select(Material).where(
        Material.company_id == company_id,
        Material.current_stock <= Material.min_stock
    )
    
    materials = session.exec(statement).all()
    return materials
