from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.models import Invoice, InvoiceItem, Material, User
from app.database import get_session
from app.auth import get_current_user
from pathlib import Path
import shutil
import os
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

# Configure upload directory
UPLOAD_DIR = Path("/opt/pvapp/data/invoices")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.xml'}

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
                price_net=item.unit_price,
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


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Upload and parse invoice file (PDF, DOC, TXT, XML)"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Parse the file
    try:
        from app.invoice_parser import parse_invoice_file, fuzzy_match_material
        
        parsed_data = parse_invoice_file(str(file_path))
        
        if "error" in parsed_data:
            raise HTTPException(status_code=400, detail=f"Error parsing file: {parsed_data['error']}")
        
        # Create invoice record
        invoice = Invoice(
            supplier=parsed_data.get("supplier"),
            invoice_number=parsed_data.get("invoice_number"),
            invoice_date=parsed_data.get("invoice_date"),
            total_amount=parsed_data.get("total_amount"),
            status="PARSED",
            file_path=str(file_path),
            file_type=file_ext.upper().replace('.', ''),
            raw_text=parsed_data.get("raw_text", "")
        )
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        
        # Get existing materials for fuzzy matching
        existing_materials = session.exec(select(Material)).all()
        materials_list = [
            {"id": m.id, "name": m.name, "category": m.category, "unit": m.unit}
            for m in existing_materials
        ]
        
        # Create invoice items with suggested material matches
        items_created = []
        for item_data in parsed_data.get("items", []):
            # Try to find matching material
            suggested_match = fuzzy_match_material(
                item_data.get("description", ""),
                materials_list
            )
            
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data.get("description"),
                quantity=item_data.get("quantity", 0.0),
                unit=item_data.get("unit"),
                unit_price=item_data.get("unit_price"),
                total_price=item_data.get("total_price"),
                suggested_material_id=suggested_match[0] if suggested_match else None,
                match_confidence=suggested_match[1] if suggested_match else None
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            items_created.append(item)
        
        # Return invoice with items and suggestions
        return {
            "message": "Invoice uploaded and parsed successfully",
            "invoice_id": invoice.id,
            "invoice": {
                "id": invoice.id,
                "supplier": invoice.supplier,
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "total_amount": invoice.total_amount,
                "status": invoice.status,
                "file_type": invoice.file_type
            },
            "items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "suggested_material_id": item.suggested_material_id,
                    "match_confidence": item.match_confidence
                }
                for item in items_created
            ],
            "items_count": len(items_created)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/{invoice_id}/validate-items")
def validate_invoice_items(
    invoice_id: int,
    validated_items: List[dict],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Validate and update invoice items with user-confirmed material mappings
    Also creates new materials if needed
    
    validated_items format:
    [
        {
            "item_id": 1,
            "material_id": 5,  # existing material
            "create_new": false
        },
        {
            "item_id": 2,
            "create_new": true,
            "new_material": {
                "name": "Material Name",
                "category": "Category",
                "unit": "pcs",
                "minimum_stock": 10
            }
        }
    ]
    """
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    created_materials = []
    updated_items = []
    
    for validation in validated_items:
        item_id = validation.get("item_id")
        item = session.get(InvoiceItem, item_id)
        
        if not item or item.invoice_id != invoice_id:
            continue
        
        if validation.get("create_new"):
            # Create new material
            new_mat_data = validation.get("new_material", {})
            new_material = Material(
                name=new_mat_data.get("name"),
                category=new_mat_data.get("category", "General"),
                unit=new_mat_data.get("unit", "pcs"),
                minimum_stock=new_mat_data.get("minimum_stock", 0),
                current_stock=0
            )
            session.add(new_material)
            session.commit()
            session.refresh(new_material)
            
            created_materials.append(new_material)
            item.material_id = new_material.id
        else:
            # Use existing material
            material_id = validation.get("material_id")
            if material_id:
                material = session.get(Material, material_id)
                if material:
                    item.material_id = material_id
        
        session.add(item)
        updated_items.append(item)
    
    # Update invoice status
    invoice.status = "VALIDATED"
    session.add(invoice)
    session.commit()
    
    return {
        "message": "Invoice items validated successfully",
        "invoice_id": invoice_id,
        "created_materials": len(created_materials),
        "updated_items": len(updated_items),
        "materials": [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category,
                "unit": m.unit
            }
            for m in created_materials
        ]
    }
