from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import List, Dict, Any
from app.models import Project, StockMovement, LaborCost, ExtraCost, Material, CompanySetting, User
from app.database import get_session
from app.auth import get_current_user
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

router = APIRouter(prefix="/api/balance", tags=["Balance & Reports"])

# Schemas
class ProjectBalance(BaseModel):
    project_id: int
    project_name: str
    client_name: str
    system_kw: float
    material_costs: float
    labor_costs: float
    extra_costs: float
    total_net: float
    vat_rate: float
    vat_amount: float
    total_with_vat: float
    cost_per_kw: float
    materials_detail: List[Dict[str, Any]]
    labor_detail: List[Dict[str, Any]]
    extra_detail: List[Dict[str, Any]]

# Helper function to get VAT rate from settings
def get_vat_rate(session: Session) -> float:
    vat_setting = session.exec(
        select(CompanySetting).where(CompanySetting.key == "vat_rate")
    ).first()
    if vat_setting:
        try:
            return float(vat_setting.value)
        except ValueError:
            return 19.0  # Default VAT rate for Romania
    return 19.0

@router.get("/{project_id}", response_model=ProjectBalance)
def get_project_balance(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Calculate complete balance for a project"""
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Calculate material costs
    material_costs_total = 0.0
    materials_detail = []
    
    movements = session.exec(
        select(StockMovement).where(StockMovement.project_id == project_id)
    ).all()
    
    for movement in movements:
        material = session.get(Material, movement.material_id)
        cost = movement.price_net if movement.price_net else 0.0
        material_costs_total += cost
        
        materials_detail.append({
            "material_name": material.name if material else "Unknown",
            "quantity": movement.quantity,
            "price_net": movement.price_net,
            "total": cost,
            "movement_type": movement.movement_type
        })
    
    # Calculate labor costs
    labor_costs_total = 0.0
    labor_detail = []
    
    labor_costs = session.exec(
        select(LaborCost).where(LaborCost.project_id == project_id)
    ).all()
    
    for labor in labor_costs:
        cost = labor.hours * labor.hourly_rate
        labor_costs_total += cost
        
        labor_detail.append({
            "description": labor.description,
            "worker_name": labor.worker_name,
            "hours": labor.hours,
            "hourly_rate": labor.hourly_rate,
            "total": cost,
            "date": str(labor.date)
        })
    
    # Calculate extra costs
    extra_costs_total = 0.0
    extra_detail = []
    
    extra_costs = session.exec(
        select(ExtraCost).where(ExtraCost.project_id == project_id)
    ).all()
    
    for extra in extra_costs:
        extra_costs_total += extra.amount
        
        extra_detail.append({
            "description": extra.description,
            "category": extra.category,
            "amount": extra.amount,
            "date": str(extra.date)
        })
    
    # Calculate totals
    total_net = material_costs_total + labor_costs_total + extra_costs_total
    vat_rate = get_vat_rate(session)
    vat_amount = total_net * (vat_rate / 100)
    total_with_vat = total_net + vat_amount
    cost_per_kw = total_with_vat / project.system_kw if project.system_kw > 0 else 0
    
    return ProjectBalance(
        project_id=project.id,
        project_name=project.name,
        client_name=project.client_name,
        system_kw=project.system_kw,
        material_costs=material_costs_total,
        labor_costs=labor_costs_total,
        extra_costs=extra_costs_total,
        total_net=total_net,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        total_with_vat=total_with_vat,
        cost_per_kw=cost_per_kw,
        materials_detail=materials_detail,
        labor_detail=labor_detail,
        extra_detail=extra_detail
    )

@router.get("/{project_id}/pdf")
def download_project_balance_pdf(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Generate and download PDF balance for a project"""
    # Get balance data
    balance = get_project_balance(project_id, session, current_user)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>Project Balance: {balance.project_name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Project info
    info_text = f"""
    <b>Client:</b> {balance.client_name}<br/>
    <b>System Size:</b> {balance.system_kw} kW<br/>
    <b>Cost per kW:</b> {balance.cost_per_kw:.2f} RON
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Summary table
    summary_data = [
        ['Category', 'Amount (RON)'],
        ['Material Costs', f'{balance.material_costs:.2f}'],
        ['Labor Costs', f'{balance.labor_costs:.2f}'],
        ['Extra Costs', f'{balance.extra_costs:.2f}'],
        ['Total Net', f'{balance.total_net:.2f}'],
        [f'VAT ({balance.vat_rate}%)', f'{balance.vat_amount:.2f}'],
        ['Total with VAT', f'{balance.total_with_vat:.2f}']
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=balance_project_{project_id}.pdf"
        }
    )
