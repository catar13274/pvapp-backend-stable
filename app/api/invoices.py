from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import List, Optional
from sqlmodel import Session, select
from app import models
from app.database import get_session
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
import io

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# Pydantic models for request/response
class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    material_id: Optional[int] = None
    description: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    suggested_material_id: Optional[int] = None
    match_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    status: str
    filename: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class InvoiceWithItemsResponse(BaseModel):
    id: int
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    status: str
    filename: Optional[str] = None
    items: List[InvoiceItemResponse]

class MaterialCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    unit: Optional[str] = "buc"

class ValidateItemsRequest(BaseModel):
    items: List[dict]  # List of {item_id, material_id or new_material data}

# Helper functions
def similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_material_match(description: str, session: Session) -> tuple[Optional[int], float]:
    """Find the best matching material for a given description"""
    if not description:
        return None, 0.0
    
    materials = session.exec(select(models.Material)).all()
    best_match = None
    best_score = 0.0
    
    for material in materials:
        if material.name:
            score = similarity_ratio(description, material.name)
            if score > best_score:
                best_score = score
                best_match = material.id
    
    # Only suggest if confidence is above threshold
    if best_score < 0.3:
        return None, 0.0
    
    return best_match, best_score

def parse_xml_invoice(file_content: bytes) -> dict:
    """Parse XML invoice file and extract data"""
    try:
        # Parse XML with proper error handling
        root = ET.fromstring(file_content.decode('utf-8'))
        
        # Extract invoice metadata - handle various XML structures
        invoice_data = {
            'supplier': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
            'items': []
        }
        
        # Try to find common XML elements (adjust based on actual XML structure)
        # Handle different XML structures gracefully
        for elem in root.iter():
            tag = elem.tag.lower()
            if 'supplier' in tag or 'vendor' in tag:
                if elem.text:
                    invoice_data['supplier'] = elem.text
            elif 'invoice' in tag and 'number' in tag:
                if elem.text:
                    invoice_data['invoice_number'] = elem.text
            elif 'date' in tag:
                if elem.text:
                    invoice_data['invoice_date'] = elem.text
            elif 'total' in tag or 'amount' in tag:
                if elem.text:
                    try:
                        invoice_data['total_amount'] = float(elem.text)
                    except ValueError:
                        pass
        
        # Try to find line items
        for item_elem in root.findall('.//*'):
            tag = item_elem.tag.lower()
            if 'item' in tag or 'line' in tag:
                item_data = {
                    'description': None,
                    'quantity': 0.0,
                    'unit': None,
                    'unit_price': None,
                    'total_price': None
                }
                
                for child in item_elem:
                    child_tag = child.tag.lower()
                    if 'description' in child_tag or 'name' in child_tag:
                        item_data['description'] = child.text
                    elif 'quantity' in child_tag or 'qty' in child_tag:
                        try:
                            item_data['quantity'] = float(child.text or 0)
                        except ValueError:
                            pass
                    elif 'unit' in child_tag and 'price' not in child_tag:
                        item_data['unit'] = child.text
                    elif 'unit' in child_tag and 'price' in child_tag:
                        try:
                            item_data['unit_price'] = float(child.text or 0)
                        except ValueError:
                            pass
                    elif 'price' in child_tag:
                        try:
                            if 'unit' in child_tag:
                                item_data['unit_price'] = float(child.text or 0)
                            else:
                                item_data['total_price'] = float(child.text or 0)
                        except ValueError:
                            pass
                
                # Calculate total_price if not present
                if item_data['total_price'] is None and item_data['unit_price'] is not None:
                    item_data['total_price'] = item_data['quantity'] * item_data['unit_price']
                
                if item_data['description'] or item_data['quantity'] > 0:
                    invoice_data['items'].append(item_data)
        
        return invoice_data
        
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"Error parsing XML file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

def parse_pdf_invoice(file_content: bytes) -> dict:
    """Parse PDF invoice file and extract data"""
    try:
        # For now, return basic structure - can be enhanced with PDF parsing
        return {
            'supplier': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
            'items': []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF file: {str(e)}")

def parse_doc_invoice(file_content: bytes) -> dict:
    """Parse DOC/DOCX invoice file and extract data"""
    try:
        # For now, return basic structure - can be enhanced with DOC parsing
        return {
            'supplier': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
            'items': []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing DOC file: {str(e)}")

def parse_txt_invoice(file_content: bytes) -> dict:
    """Parse TXT invoice file and extract data"""
    try:
        # For now, return basic structure - can be enhanced with text parsing
        return {
            'supplier': None,
            'invoice_number': None,
            'invoice_date': None,
            'total_amount': None,
            'items': []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing TXT file: {str(e)}")

# API Endpoints
@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Upload and parse invoice file"""
    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Determine file type and parse accordingly
    filename = file.filename.lower()
    if filename.endswith('.xml'):
        invoice_data = parse_xml_invoice(file_content)
    elif filename.endswith('.pdf'):
        invoice_data = parse_pdf_invoice(file_content)
    elif filename.endswith(('.doc', '.docx')):
        invoice_data = parse_doc_invoice(file_content)
    elif filename.endswith('.txt'):
        invoice_data = parse_txt_invoice(file_content)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Create invoice record
    invoice = models.Invoice(
        supplier=invoice_data.get('supplier'),
        invoice_number=invoice_data.get('invoice_number'),
        invoice_date=invoice_data.get('invoice_date'),
        total_amount=invoice_data.get('total_amount'),
        status="PENDING",
        filename=file.filename
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    
    # Create invoice items with material matching
    items = []
    for item_data in invoice_data.get('items', []):
        # Find best matching material
        suggested_material_id, match_confidence = find_best_material_match(
            item_data.get('description', ''), session
        )
        
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            description=item_data.get('description'),
            quantity=item_data.get('quantity', 0.0),
            unit=item_data.get('unit'),
            unit_price=item_data.get('unit_price'),
            total_price=item_data.get('total_price'),
            suggested_material_id=suggested_material_id,
            match_confidence=match_confidence
        )
        session.add(invoice_item)
        session.commit()
        session.refresh(invoice_item)
        items.append(invoice_item)
    
    # Return response in expected format
    return {
        "invoice": {
            "id": invoice.id,
            "supplier": invoice.supplier,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "filename": invoice.filename
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
            for item in items
        ]
    }

@router.get("/pending")
def get_pending_invoices(session: Session = Depends(get_session)):
    """Get all pending/unconfirmed invoices"""
    invoices = session.exec(
        select(models.Invoice)
        .where(models.Invoice.status.in_(["PENDING", "VALIDATED"]))
        .order_by(models.Invoice.id.desc())
    ).all()
    
    result = []
    for invoice in invoices:
        items = session.exec(
            select(models.InvoiceItem)
            .where(models.InvoiceItem.invoice_id == invoice.id)
        ).all()
        
        result.append({
            "id": invoice.id,
            "supplier": invoice.supplier,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "filename": invoice.filename,
            "items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "material_id": item.material_id,
                    "suggested_material_id": item.suggested_material_id,
                    "match_confidence": item.match_confidence
                }
                for item in items
            ]
        })
    
    return result

@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, session: Session = Depends(get_session)):
    """Get invoice details with items"""
    invoice = session.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    items = session.exec(
        select(models.InvoiceItem)
        .where(models.InvoiceItem.invoice_id == invoice_id)
    ).all()
    
    return {
        "invoice": {
            "id": invoice.id,
            "supplier": invoice.supplier,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "total_amount": invoice.total_amount,
            "status": invoice.status,
            "filename": invoice.filename,
            "created_at": str(invoice.created_at)
        },
        "items": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "material_id": item.material_id,
                "suggested_material_id": item.suggested_material_id,
                "match_confidence": item.match_confidence
            }
            for item in items
        ]
    }

@router.put("/{invoice_id}/items/{item_id}")
def map_invoice_item_to_material(
    invoice_id: int,
    item_id: int,
    material_id: int = Query(...),
    session: Session = Depends(get_session)
):
    """Map an invoice item to a material"""
    invoice = session.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    item = session.get(models.InvoiceItem, item_id)
    if not item or item.invoice_id != invoice_id:
        raise HTTPException(status_code=404, detail="Invoice item not found")
    
    # Verify material exists
    material = session.get(models.Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update item mapping
    item.material_id = material_id
    session.add(item)
    session.commit()
    
    return {"success": True, "item_id": item_id, "material_id": material_id}

@router.post("/{invoice_id}/validate-items")
def validate_invoice_items(
    invoice_id: int,
    payload: ValidateItemsRequest,
    session: Session = Depends(get_session)
):
    """Batch validate items - create new materials if needed and map items"""
    invoice = session.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    created_materials = 0
    updated_items = 0
    
    for item_data in payload.items:
        item_id = item_data.get('item_id')
        item = session.get(models.InvoiceItem, item_id)
        
        if not item or item.invoice_id != invoice_id:
            continue
        
        # Check if we need to create a new material
        if item_data.get('create_material'):
            new_material = models.Material(
                name=item_data.get('material_name', item.description),
                sku=item_data.get('material_sku'),
                unit=item_data.get('material_unit', item.unit or 'buc')
            )
            session.add(new_material)
            session.commit()
            session.refresh(new_material)
            
            item.material_id = new_material.id
            created_materials += 1
        elif item_data.get('material_id'):
            # Map to existing material
            item.material_id = item_data.get('material_id')
        
        session.add(item)
        updated_items += 1
    
    session.commit()
    
    # Update invoice status to VALIDATED
    invoice.status = "VALIDATED"
    session.add(invoice)
    session.commit()
    
    return {
        "created_materials": created_materials,
        "updated_items": updated_items
    }

@router.post("/{invoice_id}/confirm")
def confirm_invoice(invoice_id: int, session: Session = Depends(get_session)):
    """Confirm invoice and create stock movements"""
    invoice = session.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status == "CONFIRMED":
        raise HTTPException(status_code=400, detail="Invoice already confirmed")
    
    # Get all items
    items = session.exec(
        select(models.InvoiceItem)
        .where(models.InvoiceItem.invoice_id == invoice_id)
    ).all()
    
    items_processed = 0
    
    # Create stock movements for all mapped items
    for item in items:
        if item.material_id:
            stock_movement = models.StockMovement(
                material_id=item.material_id,
                change=item.quantity,
                movement_type="invoice_in",
                reference_type="invoice",
                reference_id=invoice_id,
                quantity=item.quantity
            )
            session.add(stock_movement)
            items_processed += 1
    
    session.commit()
    
    # Update invoice status to CONFIRMED
    invoice.status = "CONFIRMED"
    session.add(invoice)
    session.commit()
    
    return {"items_processed": items_processed}
