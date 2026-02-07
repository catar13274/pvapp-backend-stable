from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlmodel import Session, select
from app import models
from app.database import get_session
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/purchases", tags=["purchases"])

class PurchaseItemCreate(BaseModel):
    material_id: Optional[int] = None
    sku_raw: Optional[str] = None
    sku_clean: Optional[str] = None
    description: Optional[str] = None
    quantity: float
    unit_price: float

class PurchaseCreate(BaseModel):
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    items: List[PurchaseItemCreate]

class PurchaseItemRead(BaseModel):
    id: int
    purchase_id: int
    material_id: Optional[int]
    sku_raw: Optional[str]
    sku_clean: Optional[str]
    description: Optional[str]
    quantity: float
    unit_price: Optional[float]
    total_price: Optional[float]
    class Config:
        from_attributes = True

class PurchaseRead(BaseModel):
    id: int
    supplier: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    total_amount: Optional[float]
    created_at: str
    class Config:
        from_attributes = True

@router.get("/", response_model=List[PurchaseRead], operation_id="list_purchases")
def list_purchases(session: Session = Depends(get_session)):
    purchases = session.exec(select(models.Purchase).order_by(models.Purchase.id.desc())).all()
    return purchases

@router.post("/", status_code=201, operation_id="create_purchase")
def create_purchase(payload: PurchaseCreate, session: Session = Depends(get_session)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="items required")

    items_total = sum(i.quantity * i.unit_price for i in payload.items)
    purchase_total = payload.total_amount or items_total

    purchase = models.Purchase(
        supplier=payload.supplier,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        total_amount=purchase_total
    )
    session.add(purchase)
    session.commit()
    session.refresh(purchase)

    for it in payload.items:
        pi = models.PurchaseItem(
            purchase_id=purchase.id,
            material_id=it.material_id,
            sku_raw=it.sku_raw,
            sku_clean=it.sku_clean,
            description=it.description,
            quantity=it.quantity,
            unit_price=it.unit_price,
            total_price=(it.quantity * it.unit_price)
        )
        session.add(pi)
        session.commit()
        session.refresh(pi)

        if it.material_id is not None:
            sm = models.StockMovement(
                material_id=it.material_id,
                change=it.quantity,
                movement_type="purchase_in",
                reference_type="purchase",
                reference_id=purchase.id,
                quantity=it.quantity
            )
            session.add(sm)
            session.commit()

    return {"id": purchase.id, "created_at": str(purchase.created_at)}

@router.get("/{purchase_id}", operation_id="get_purchase_detail")
def get_purchase_detail(purchase_id: int, session: Session = Depends(get_session)):
    purchase = session.get(models.Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Not Found")

    items = session.exec(select(models.PurchaseItem).where(models.PurchaseItem.purchase_id == purchase_id)).all()
    result_items = []
    for it in items:
        mat = None
        if it.material_id:
            mat = session.get(models.Material, it.material_id)
        result_items.append({
            "id": it.id,
            "purchase_id": it.purchase_id,
            "material_id": it.material_id,
            "sku_raw": it.sku_raw,
            "sku_clean": it.sku_clean,
            "description": it.description,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
            "total_price": it.total_price,
            "material": {"id": mat.id, "sku": mat.sku, "name": mat.name} if mat else None
        })

    return {"purchase": purchase, "items": result_items}
