from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

# Company Model pentru Multi-Company Support
class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

# User Model cu company relationship
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    sku: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = "buc"
    current_stock: float = 0.0
    min_stock: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    efactura_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PurchaseItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: int = Field(foreign_key="purchase.id")
    material_id: Optional[int] = Field(default=None, foreign_key="material.id")
    sku_raw: Optional[str] = None
    sku_clean: Optional[str] = None
    description: Optional[str] = None
    quantity: float = 0.0
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

class StockMovement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    company_id: int = Field(foreign_key="company.id")
    change: float = 0.0
    movement_type: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    quantity: Optional[float] = None

# Make.com Webhook Log
class WebhookLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    webhook_type: str
    payload: str
    status: str = "pending"
    response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None