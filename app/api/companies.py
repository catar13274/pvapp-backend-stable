"""
Company Management API
Multi-company support endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List

from app.models import Company, User
from app.database import get_session

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/", response_model=List[Company])
async def list_companies(session: Session = Depends(get_session)):
    """List all companies"""
    statement = select(Company).where(Company.active == True)
    companies = session.exec(statement).all()
    return companies

@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: int, session: Session = Depends(get_session)):
    """Get company by ID"""
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/", response_model=Company)
async def create_company(company: Company, session: Session = Depends(get_session)):
    """Create new company"""
    session.add(company)
    session.commit()
    session.refresh(company)
    return company

@router.put("/{company_id}", response_model=Company)
async def update_company(
    company_id: int,
    company_data: Company,
    session: Session = Depends(get_session)
):
    """Update company"""
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company_data_dict = company_data.dict(exclude_unset=True)
    for key, value in company_data_dict.items():
        setattr(company, key, value)
    
    session.commit()
    session.refresh(company)
    return company

@router.delete("/{company_id}")
async def delete_company(company_id: int, session: Session = Depends(get_session)):
    """Soft delete company"""
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.active = False
    session.commit()
    
    return {"message": "Company deactivated successfully"}