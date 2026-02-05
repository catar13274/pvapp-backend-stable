"""
Purchases Management API
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List

from app.models import Purchase, PurchaseItem
from app.database import get_session

router = APIRouter(prefix="/purchases", tags=["Purchases"])

@router.get("/", response_model=List[Purchase])
async def list_purchases(
    company_id: int,
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
):
    """List all purchases for a company"""
    statement = select(Purchase).where(
        Purchase.company_id == company_id
    ).offset(skip).limit(limit)
    purchases = session.exec(statement).all()
    return purchases

@router.get("/{purchase_id}", response_model=Purchase)
async def get_purchase(purchase_id: int, session: Session = Depends(get_session)):
    """Get purchase by ID"""
    purchase = session.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return purchase

@router.post("/", response_model=Purchase)
async def create_purchase(purchase: Purchase, session: Session = Depends(get_session)):
    """Create new purchase"""
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    return purchase

@router.get("/{purchase_id}/items")
async def get_purchase_items(
    purchase_id: int,
    session: Session = Depends(get_session)
):
    """Get all items for a purchase"""
    statement = select(PurchaseItem).where(
        PurchaseItem.purchase_id == purchase_id
    )
    items = session.exec(statement).all()
    return items

@router.post("/{purchase_id}/items")
async def add_purchase_item(
    purchase_id: int,
    item: PurchaseItem,
    session: Session = Depends(get_session)
):
    """Add item to purchase"""
    purchase = session.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    item.purchase_id = purchase_id
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
