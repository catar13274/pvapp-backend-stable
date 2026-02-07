from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = "buc"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
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
    change: float = 0.0
    movement_type: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    quantity: Optional[float] = None

class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    status: str = "PENDING"  # PENDING, VALIDATED, CONFIRMED
    filename: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id")
    material_id: Optional[int] = Field(default=None, foreign_key="material.id")
    description: Optional[str] = None
    quantity: float = 0.0
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    suggested_material_id: Optional[int] = None
    match_confidence: Optional[float] = None
