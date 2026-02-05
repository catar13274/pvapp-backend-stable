"""
Make.com Webhook Integration
Handles incoming webhooks from Make.com automation platform
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session
from typing import Dict, Any
import json
from datetime import datetime

from app.models import WebhookLog, Purchase, Material, Company
from app.database import get_session

router = APIRouter(prefix="/webhooks/make", tags=["Make.com"])

@router.post("/invoice")
async def receive_invoice_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Receive invoice data from Make.com
    Expected payload:
    {
        "company_id": 1,
        "supplier": "Supplier Name",
        "invoice_number": "INV-001",
        "invoice_date": "2026-01-01",
        "total_amount": 1000.00,
        "items": [
            {
                "description": "Item 1",
                "quantity": 10,
                "unit_price": 100.00
            }
        ]
    }
    """
    try:
        payload = await request.json()
        
        # Log webhook
        webhook_log = WebhookLog(
            company_id=payload.get("company_id", 0),
            webhook_type="invoice",
            payload=json.dumps(payload),
            status="processing"
        )
        session.add(webhook_log)
        session.commit()
        
        # Validate company
        company = session.get(Company, payload.get("company_id"))
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Create purchase
        purchase = Purchase(
            company_id=company.id,
            supplier=payload.get("supplier"),
            invoice_number=payload.get("invoice_number"),
            invoice_date=payload.get("invoice_date"),
            total_amount=payload.get("total_amount", 0.0)
        )
        session.add(purchase)
        session.commit()
        session.refresh(purchase)
        
        # Create purchase items
        from app.models import PurchaseItem
        for item in payload.get("items", []):
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                description=item.get("description"),
                quantity=item.get("quantity", 0),
                unit_price=item.get("unit_price", 0),
                total_price=item.get("quantity", 0) * item.get("unit_price", 0)
            )
            session.add(purchase_item)
        
        session.commit()
        
        # Update webhook log
        webhook_log.status = "completed"
        webhook_log.response = json.dumps({"purchase_id": purchase.id})
        webhook_log.processed_at = datetime.utcnow()
        session.commit()
        
        return {
            "status": "success",
            "purchase_id": purchase.id,
            "message": "Invoice processed successfully"
        }
        
    except Exception as e:
        if 'webhook_log' in locals():
            webhook_log.status = "failed"
            webhook_log.response = str(e)
            session.commit()
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material-update")
async def receive_material_update_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Receive material updates from Make.com
    Expected payload:
    {
        "company_id": 1,
        "material_id": 5,
        "updates": {
            "name": "Updated Name",
            "sku": "NEW-SKU",
            "min_stock": 50
        }
    }
    """
    try:
        payload = await request.json()
        
        # Log webhook
        webhook_log = WebhookLog(
            company_id=payload.get("company_id", 0),
            webhook_type="material_update",
            payload=json.dumps(payload),
            status="processing"
        )
        session.add(webhook_log)
        session.commit()
        
        # Get material
        material = session.get(Material, payload.get("material_id"))
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Update material
        updates = payload.get("updates", {})
        for key, value in updates.items():
            if hasattr(material, key):
                setattr(material, key, value)
        
        session.commit()
        session.refresh(material)
        
        # Update webhook log
        webhook_log.status = "completed"
        webhook_log.response = json.dumps({"material_id": material.id})
        webhook_log.processed_at = datetime.utcnow()
        session.commit()
        
        return {
            "status": "success",
            "material_id": material.id,
            "message": "Material updated successfully"
        }
        
    except Exception as e:
        if 'webhook_log' in locals():
            webhook_log.status = "failed"
            webhook_log.response = str(e)
            session.commit()
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock-alert")
async def receive_stock_alert_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Receive stock alert notifications from Make.com
    """
    try:
        payload = await request.json()
        
        # Log webhook
        webhook_log = WebhookLog(
            company_id=payload.get("company_id", 0),
            webhook_type="stock_alert",
            payload=json.dumps(payload),
            status="completed",
            processed_at=datetime.utcnow()
        )
        session.add(webhook_log)
        session.commit()
        
        return {
            "status": "success",
            "message": "Stock alert logged"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/{company_id}")
async def get_webhook_logs(
    company_id: int,
    session: Session = Depends(get_session),
    limit: int = 50
):
    """Get webhook logs for a company"""
    from sqlmodel import select
    
    statement = select(WebhookLog).where(
        WebhookLog.company_id == company_id
    ).order_by(WebhookLog.created_at.desc()).limit(limit)
    
    logs = session.exec(statement).all()
    
    return {
        "company_id": company_id,
        "logs": logs
    }