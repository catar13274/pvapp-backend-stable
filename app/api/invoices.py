"""
Invoice upload and XML parsing endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlmodel import Session
import httpx
from app import models
from app.database import get_session
from app.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


async def call_xml_parser(xml_content: bytes, filename: str) -> dict:
    """
    Call the XML parser microservice to parse the invoice.
    
    Args:
        xml_content: Raw XML file content
        filename: Name of the uploaded file
        
    Returns:
        Parsed invoice data as dict
        
    Raises:
        HTTPException: If parser service fails or is not configured
    """
    if not config.XML_PARSER_URL:
        raise HTTPException(
            status_code=503, 
            detail="XML parser service not configured. Set XML_PARSER_URL environment variable."
        )
    
    parser_url = f"{config.XML_PARSER_URL.rstrip('/')}/parse"
    
    try:
        # Prepare headers
        headers = {}
        if config.XML_PARSER_TOKEN:
            headers['Authorization'] = f'Bearer {config.XML_PARSER_TOKEN}'
        
        # Send file to parser service
        files = {'file': (filename, xml_content, 'application/xml')}
        
        async with httpx.AsyncClient(timeout=config.XML_PARSER_TIMEOUT) as client:
            logger.info(f"Calling XML parser at {parser_url} for file {filename}")
            response = await client.post(parser_url, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully parsed {filename}")
                return result
            elif response.status_code == 401:
                logger.error("XML parser authentication failed")
                raise HTTPException(status_code=502, detail="Parser service authentication failed")
            else:
                error_detail = response.json().get('error', 'Unknown error') if response.text else 'Unknown error'
                logger.error(f"Parser service error: {error_detail}")
                raise HTTPException(
                    status_code=502, 
                    detail=f"Parser service error: {error_detail}"
                )
                
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except httpx.TimeoutException:
        logger.error(f"Timeout calling XML parser for {filename}")
        raise HTTPException(status_code=504, detail="Parser service timeout")
    except httpx.RequestError as e:
        logger.error(f"Request error calling XML parser: {e}")
        raise HTTPException(status_code=502, detail=f"Cannot connect to parser service: {e}")
    except Exception as e:
        logger.error(f"Unexpected error calling XML parser: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


def create_purchase_from_parsed_xml(parsed_data: dict, session: Session) -> models.Purchase:
    """
    Create a Purchase record from parsed XML invoice data.
    
    Args:
        parsed_data: Parsed invoice data from XML parser
        session: Database session
        
    Returns:
        Created Purchase record
    """
    metadata = parsed_data.get('data', {}).get('invoice_metadata', {})
    line_items = parsed_data.get('data', {}).get('line_items', [])
    
    # Create Purchase record
    purchase = models.Purchase(
        supplier=metadata.get('supplier'),
        invoice_number=metadata.get('invoice_number'),
        invoice_date=metadata.get('invoice_date'),
        total_amount=metadata.get('total_amount')
    )
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    
    logger.info(f"Created purchase {purchase.id} from XML invoice")
    
    # Create PurchaseItem records
    for item_data in line_items:
        purchase_item = models.PurchaseItem(
            purchase_id=purchase.id,
            sku_raw=item_data.get('sku_raw'),
            description=item_data.get('description'),
            quantity=item_data.get('quantity', 0.0),
            unit_price=item_data.get('unit_price'),
            total_price=item_data.get('total_price')
        )
        session.add(purchase_item)
    
    session.commit()
    logger.info(f"Created {len(line_items)} purchase items for purchase {purchase.id}")
    
    return purchase


@router.post("/upload", status_code=201)
async def upload_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload an invoice file (XML or other formats).
    
    For XML files:
    - Detects XML by file extension or MIME type
    - Calls XML parser microservice for parsing
    - Creates Purchase and PurchaseItem records from parsed data
    
    For other formats:
    - Returns error (not yet implemented)
    """
    # Read file content
    content = await file.read()
    
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Detect XML files
    is_xml = (
        file.filename and file.filename.lower().endswith('.xml') or
        file.content_type and 'xml' in file.content_type.lower()
    )
    
    if not is_xml:
        raise HTTPException(
            status_code=400, 
            detail="Only XML invoice files are currently supported"
        )
    
    logger.info(f"Processing XML invoice upload: {file.filename}, size: {len(content)} bytes")
    
    # Parse XML using microservice
    try:
        parsed_data = await call_xml_parser(content, file.filename or "invoice.xml")
    except HTTPException:
        # Re-raise HTTP exceptions from parser
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing XML: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse XML: {e}")
    
    # Create purchase records from parsed data
    try:
        purchase = create_purchase_from_parsed_xml(parsed_data, session)
        
        return {
            "success": True,
            "message": "Invoice uploaded and parsed successfully",
            "purchase_id": purchase.id,
            "invoice_number": purchase.invoice_number,
            "supplier": purchase.supplier,
            "total_amount": purchase.total_amount,
            "items_count": len(parsed_data.get('data', {}).get('line_items', []))
        }
        
    except Exception as e:
        logger.error(f"Error creating purchase from parsed XML: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create purchase: {e}")


@router.get("/health")
def invoice_health():
    """Health check for invoice endpoints."""
    parser_configured = config.XML_PARSER_URL is not None
    return {
        "status": "healthy",
        "xml_parser_configured": parser_configured,
        "xml_parser_url": config.XML_PARSER_URL if parser_configured else None
    }
