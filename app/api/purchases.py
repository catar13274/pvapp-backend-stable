from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from sqlmodel import Session, select
from app import models
from app.database import get_session
from pydantic import BaseModel
from app.parsers.invoice_xml import parse_invoice_products

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
        orm_mode = True

class PurchaseRead(BaseModel):
    id: int
    supplier: Optional[str]
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    total_amount: Optional[float]
    created_at: str
    class Config:
        orm_mode = True

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

@router.post("/upload-xml", status_code=201, operation_id="upload_invoice_xml")
async def upload_invoice_xml(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload și parsare automată a facturii XML în format UBL (e-Factura RO).
    Creează automat un purchase cu toate produsele din factură.
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Doar fișiere XML sunt acceptate")
    
    # Citește conținutul fișierului
    xml_content = await file.read()
    
    try:
        # Parsează XML-ul
        invoice_data = parse_invoice_products(xml_content.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Eroare la parsarea XML: {str(e)}")
    
    if not invoice_data["products"]:
        raise HTTPException(status_code=400, detail="Nu s-au găsit produse în factură")
    
    # Creează purchase-ul
    purchase = models.Purchase(
        supplier=invoice_data["supplier"],
        invoice_number=invoice_data["invoice_number"],
        invoice_date=invoice_data["invoice_date"],
        total_amount=invoice_data["total_amount"]
    )
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    
    # Creează items pentru fiecare produs
    created_items = []
    new_materials = []
    purchase_items = []
    stock_movements = []
    material_cache = {}  # Cache pentru a evita query-uri redundante
    
    # Prima trecere: caută materialele existente și creează cele noi
    for product in invoice_data["products"]:
        # Încearcă să găsești material după SKU
        material = None
        if product["sku"]:
            material = session.exec(
                select(models.Material).where(models.Material.sku == product["sku"])
            ).first()
            if material:
                material_cache[product["sku"]] = material
        
        # Dacă nu există material, creează unul nou
        if not material and product["name"]:
            material = models.Material(
                sku=product["sku"] or None,
                name=product["name"],
                unit=product["unit"]
            )
            new_materials.append((product["sku"], material))
            session.add(material)
    
    # Commit toate materialele noi odată
    if new_materials:
        session.commit()
        for sku, material in new_materials:
            session.refresh(material)
            if sku:
                material_cache[sku] = material
    
    # A doua trecere: creează purchase items și stock movements
    for product in invoice_data["products"]:
        # Folosește cache-ul pentru a obține materialul
        material = material_cache.get(product["sku"]) if product["sku"] else None
        
        # Creează purchase item
        pi = models.PurchaseItem(
            purchase_id=purchase.id,
            material_id=material.id if material else None,
            sku_raw=product["sku"],
            sku_clean=product["sku"],
            description=product["name"],
            quantity=product["quantity"],
            unit_price=product["unit_price"],
            total_price=product["total_price"]
        )
        purchase_items.append(pi)
        session.add(pi)
        
        # Creează stock movement dacă există material
        if material:
            sm = models.StockMovement(
                material_id=material.id,
                change=product["quantity"],
                movement_type="purchase_in",
                reference_type="purchase",
                reference_id=purchase.id,
                quantity=product["quantity"]
            )
            stock_movements.append(sm)
            session.add(sm)
    
    # Commit toate purchase items și stock movements odată
    session.commit()
    for pi in purchase_items:
        session.refresh(pi)
        created_items.append({
            "id": pi.id,
            "material_id": pi.material_id,
            "description": pi.description,
            "quantity": pi.quantity
        })
    
    return {
        "success": True,
        "purchase_id": purchase.id,
        "invoice_number": invoice_data["invoice_number"],
        "supplier": invoice_data["supplier"],
        "total_amount": invoice_data["total_amount"],
        "items_created": len(created_items),
        "items": created_items
    }
