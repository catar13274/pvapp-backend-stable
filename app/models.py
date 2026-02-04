from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    INSTALLER = "INSTALLER"

class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MovementType(str, Enum):
    IN = "IN"
    OUT = "OUT"

# User model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="INSTALLER")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Material model
class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    unit: str
    minimum_stock: float = 0
    current_stock: float = 0
    sku: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Material Price model
class MaterialPrice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    price_net: float
    supplier: str
    invoice_number: str
    date: datetime = Field(default_factory=datetime.utcnow)

# Project model
class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    client_name: str
    client_address: str
    system_kw: float
    status: str = Field(default="PLANNING")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

# Stock Movement model
class StockMovement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    movement_type: str  # IN or OUT
    quantity: float
    price_net: Optional[float] = None
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Legacy fields for compatibility
    change: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None

# Labor Cost model
class LaborCost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    description: str
    hours: float
    hourly_rate: float
    worker_name: str
    date: datetime = Field(default_factory=datetime.utcnow)

# Extra Cost model
class ExtraCost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    description: str
    amount: float
    category: str
    date: datetime = Field(default_factory=datetime.utcnow)

# Company Setting model
class CompanySetting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Invoice models (enhanced for file upload)
class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    status: str = Field(default="PENDING")  # PENDING, PARSED, VALIDATED, CONFIRMED
    file_path: Optional[str] = None  # Path to uploaded file
    file_type: Optional[str] = None  # PDF, DOC, TXT, XML
    raw_text: Optional[str] = None  # Extracted text from file
    created_at: datetime = Field(default_factory=datetime.utcnow)

class InvoiceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoice.id")
    material_id: Optional[int] = Field(default=None, foreign_key="material.id")
    description: Optional[str] = None
    quantity: float = 0.0
    unit: Optional[str] = None  # Unit of measurement
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    suggested_material_id: Optional[int] = None  # AI/fuzzy matched material
    match_confidence: Optional[float] = None  # Confidence score for match

# Legacy Purchase models (keep for compatibility)
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
