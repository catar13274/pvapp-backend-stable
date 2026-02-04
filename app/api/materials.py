from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models import Material, MaterialPrice, User
from app.database import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/materials", tags=["Materials"])

# Schemas
class MaterialCreate(BaseModel):
    name: str
    category: str
    unit: str
    minimum_stock: float = 0

class MaterialResponse(BaseModel):
    id: int
    name: str
    category: str
    unit: str
    minimum_stock: float
    current_stock: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MaterialPriceCreate(BaseModel):
    material_id: int
    price_net: float
    supplier: str
    invoice_number: str

class MaterialPriceResponse(BaseModel):
    id: int
    material_id: int
    price_net: float
    supplier: str
    invoice_number: str
    date: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Endpoints
@router.post("/", response_model=MaterialResponse, status_code=201)
def create_material(
    material_data: MaterialCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new material"""
    db_material = Material(**material_data.dict())
    session.add(db_material)
    session.commit()
    session.refresh(db_material)
    return db_material

@router.get("/", response_model=List[MaterialResponse])
def get_materials(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all materials"""
    materials = session.exec(select(Material).offset(skip).limit(limit)).all()
    return materials

@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get material by ID"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_data: MaterialCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    for key, value in material_data.dict().items():
        setattr(material, key, value)
    
    session.add(material)
    session.commit()
    session.refresh(material)
    return material

@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete material"""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    session.delete(material)
    session.commit()
    return {"message": "Material deleted successfully"}

@router.post("/prices", response_model=MaterialPriceResponse, status_code=201)
def create_material_price(
    price_data: MaterialPriceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create material price entry"""
    # Verify material exists
    material = session.get(Material, price_data.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    db_price = MaterialPrice(**price_data.dict())
    session.add(db_price)
    session.commit()
    session.refresh(db_price)
    return db_price

@router.get("/{material_id}/prices", response_model=List[MaterialPriceResponse])
def get_material_prices(
    material_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get price history for a material"""
    # Verify material exists
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    prices = session.exec(
        select(MaterialPrice)
        .where(MaterialPrice.material_id == material_id)
        .order_by(MaterialPrice.date.desc())
    ).all()
    return prices

@router.get("/low-stock/alert")
def get_low_stock_materials(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get materials with stock below minimum"""
    low_stock_materials = session.exec(
        select(Material).where(Material.current_stock < Material.minimum_stock)
    ).all()
    
    return {
        "count": len(low_stock_materials),
        "materials": [
            {
                "id": m.id,
                "name": m.name,
                "current_stock": m.current_stock,
                "minimum_stock": m.minimum_stock,
                "deficit": m.minimum_stock - m.current_stock
            }
            for m in low_stock_materials
        ]
    }
