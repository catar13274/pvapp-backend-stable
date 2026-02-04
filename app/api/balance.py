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
    """Generate and download PDF balance for a project with detailed materials"""
    from datetime import datetime
    
    # Get balance data
    balance = get_project_balance(project_id, session, current_user)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Commercial Offer Header
    header_text = f"""
    <para align=center>
    <b><font size=16>COMMERCIAL OFFER</font></b><br/>
    <font size=10>Offer #: PROJ-{project_id:04d}</font><br/>
    <font size=10>Date: {datetime.now().strftime('%Y-%m-%d')}</font>
    </para>
    """
    elements.append(Paragraph(header_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Client Information
    elements.append(Paragraph("<b><font size=12>CLIENT INFORMATION</font></b>", styles['Normal']))
    elements.append(Spacer(1, 6))
    client_info = f"""
    <b>Client:</b> {balance.client_name}<br/>
    <b>Project:</b> {balance.project_name}<br/>
    <b>System Size:</b> {balance.system_kw} kW
    """
    elements.append(Paragraph(client_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # MATERIALS SECTION
    if balance.materials_detail:
        elements.append(Paragraph("<b><font size=12>MATERIALS USED</font></b>", styles['Normal']))
        elements.append(Spacer(1, 6))
        
        materials_data = [['Material', 'Qty', 'Unit', 'Unit Price', 'Total (RON)']]
        for item in balance.materials_detail:
            materials_data.append([
                item['material_name'],
                str(item['quantity']),
                '-',
                f"{item['price_net']:.2f}" if item['price_net'] else '0.00',
                f"{item['total']:.2f}"
            ])
        materials_data.append(['', '', '', 'Subtotal:', f'{balance.material_costs:.2f}'])
        
        materials_table = Table(materials_data, colWidths=[200, 50, 50, 80, 80])
        materials_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(materials_table)
        elements.append(Spacer(1, 20))
    
    # LABOR SECTION
    if balance.labor_detail:
        elements.append(Paragraph("<b><font size=12>LABOR COSTS</font></b>", styles['Normal']))
        elements.append(Spacer(1, 6))
        
        labor_data = [['Description', 'Worker', 'Hours', 'Rate', 'Total (RON)', 'Date']]
        for item in balance.labor_detail:
            labor_data.append([
                item['description'][:30],
                item['worker_name'][:15],
                str(item['hours']),
                f"{item['hourly_rate']:.2f}",
                f"{item['total']:.2f}",
                item['date'][:10]
            ])
        labor_data.append(['', '', '', '', f'{balance.labor_costs:.2f}', 'Subtotal'])
        
        labor_table = Table(labor_data, colWidths=[120, 80, 40, 60, 80, 80])
        labor_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(labor_table)
        elements.append(Spacer(1, 20))
    
    # EXTRA COSTS SECTION
    if balance.extra_detail:
        elements.append(Paragraph("<b><font size=12>EXTRA COSTS</font></b>", styles['Normal']))
        elements.append(Spacer(1, 6))
        
        extra_data = [['Description', 'Category', 'Amount (RON)', 'Date']]
        for item in balance.extra_detail:
            extra_data.append([
                item['description'][:40],
                item['category'][:20],
                f"{item['amount']:.2f}",
                item['date'][:10]
            ])
        extra_data.append(['', 'Subtotal:', f'{balance.extra_costs:.2f}', ''])
        
        extra_table = Table(extra_data, colWidths=[200, 100, 100, 80])
        extra_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(extra_table)
        elements.append(Spacer(1, 20))
    
    # FINANCIAL SUMMARY
    elements.append(Paragraph("<b><font size=12>FINANCIAL SUMMARY</font></b>", styles['Normal']))
    elements.append(Spacer(1, 6))
    
    summary_data = [
        ['Category', 'Amount (RON)'],
        ['Materials', f'{balance.material_costs:.2f}'],
        ['Labor', f'{balance.labor_costs:.2f}'],
        ['Extra Costs', f'{balance.extra_costs:.2f}'],
        ['', ''],
        ['Subtotal (Net)', f'{balance.total_net:.2f}'],
        [f'VAT ({balance.vat_rate}%)', f'{balance.vat_amount:.2f}'],
        ['', ''],
        ['TOTAL WITH VAT', f'{balance.total_with_vat:.2f}'],
        ['Cost per kW', f'{balance.cost_per_kw:.2f}']
    ]
    
    summary_table = Table(summary_data, colWidths=[350, 110])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -2), (-1, -2), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEABOVE', (0, 5), (-1, 5), 2, colors.black),
        ('LINEABOVE', (0, 8), (-1, 8), 2, colors.black)
    ]))
    
    elements.append(summary_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=offer_project_{project_id}.pdf"
        }
    )
