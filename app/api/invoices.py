from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import Invoice, InvoiceItem, Material, User
from app.database import get_session
from app.auth import get_current_user

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

@router.get("/pending")
def get_pending_invoices(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get pending invoices"""
    pending_invoices = session.exec(
        select(Invoice).where(Invoice.status == "PENDING")
    ).all()
    
    result = []
    for invoice in pending_invoices:
        items = session.exec(
            select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)
        ).all()
        
        result.append({
            "id": invoice.id,
            "supplier": invoice.supplier,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "created_at": str(invoice.created_at),
            "items": [
                {
                    "id": item.id,
                    "material_id": item.material_id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in items
            ]
        })
    
    return result

@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get invoice details"""
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    ).all()
    
    return {
        "id": invoice.id,
        "supplier": invoice.supplier,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "created_at": str(invoice.created_at),
        "items": [
            {
                "id": item.id,
                "material_id": item.material_id,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price
            }
            for item in items
        ]
    }

@router.put("/{invoice_id}/items/{item_id}")
def map_invoice_item(
    invoice_id: int,
    item_id: int,
    material_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Map an invoice item to a material"""
    # Verify invoice exists
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Verify item exists
    item = session.get(InvoiceItem, item_id)
    if not item or item.invoice_id != invoice_id:
        raise HTTPException(status_code=404, detail="Invoice item not found")
    
    # Verify material exists
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Map the item to the material
    item.material_id = material_id
    session.add(item)
    session.commit()
    
    return {
        "message": "Invoice item mapped to material successfully",
        "item_id": item_id,
        "material_id": material_id
    }

@router.post("/{invoice_id}/confirm")
def confirm_invoice(
    invoice_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Confirm an invoice and create stock movements"""
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status == "CONFIRMED":
        raise HTTPException(status_code=400, detail="Invoice already confirmed")
    
    # Get all items
    items = session.exec(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id)
    ).all()
    
    # Check if all items are mapped
    unmapped_items = [item for item in items if item.material_id is None]
    if unmapped_items:
        raise HTTPException(
            status_code=400,
            detail=f"{len(unmapped_items)} items are not mapped to materials"
        )
    
    # Create stock movements for each item
    from app.models import StockMovement
    
    for item in items:
        # Update material stock
        material = session.get(Material, item.material_id)
        if material:
            material.current_stock += item.quantity
            session.add(material)
            
            # Create stock movement
            movement = StockMovement(
                material_id=item.material_id,
                movement_type="IN",
                quantity=item.quantity,
                price_net=item.unit_price * item.quantity if item.unit_price else 0,
                invoice_number=invoice.invoice_number,
                notes=f"From invoice {invoice.invoice_number}",
                created_by=current_user.id
            )
            session.add(movement)
    
    # Update invoice status
    invoice.status = "CONFIRMED"
    session.add(invoice)
    session.commit()
    
    return {
        "message": "Invoice confirmed successfully",
        "invoice_id": invoice_id,
        "items_processed": len(items)
    }
