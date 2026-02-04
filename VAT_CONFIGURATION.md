# VAT Configuration Guide

## Overview

This guide explains how VAT (TVA in Romanian) is configured and used in the PV Management App.

**Requirement:** "tva ul sa fie configurabil" (VAT should be configurable)

## Current Implementation

### Storage

VAT rate is stored in the `company_setting` table:

```python
class CompanySetting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True)
    value: str
    description: Optional[str]
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**VAT Setting:**
- Key: `"vat_rate"`
- Value: `"19"` (default for Romania)
- Description: `"VAT rate percentage (Romania default)"`

### Default Value

During database initialization (`scripts/init_db.py`):
```python
vat = CompanySetting(
    key="vat_rate",
    value="19",
    description="VAT rate percentage (Romania default)"
)
```

**Romanian VAT Rates:**
- Standard rate: 19%
- Reduced rate: 9% (certain goods/services)
- Super-reduced rate: 5% (specific items)

## Configuration Methods

### Method 1: Via API

**Get Current VAT Rate:**
```bash
curl http://localhost:8000/api/settings/vat_rate \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
    "key": "vat_rate",
    "value": "19",
    "description": "VAT rate percentage (Romania default)",
    "id": 1,
    "updated_at": "2024-01-15T10:00:00"
}
```

**Update VAT Rate:**
```bash
curl -X POST http://localhost:8000/api/settings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "vat_rate",
    "value": "9",
    "description": "Reduced VAT rate"
  }'
```

### Method 2: Via Web Interface

1. Login to the application
2. Navigate to **Settings** page
3. Find **VAT Rate** field
4. Enter new percentage (e.g., 19, 9, or 5)
5. Click **Save**

**UI Input:**
```
┌──────────────────────────────┐
│ VAT Rate: [19] %  [Save]    │
└──────────────────────────────┘
```

### Method 3: Direct Database

```sql
-- View current VAT rate
SELECT * FROM company_setting WHERE key = 'vat_rate';

-- Update VAT rate to 9%
UPDATE company_setting 
SET value = '9', updated_at = CURRENT_TIMESTAMP
WHERE key = 'vat_rate';
```

## Usage in Application

### Balance Calculation

VAT is used when calculating project balances (`app/api/balance.py`):

```python
def get_vat_rate(session: Session) -> float:
    """Get VAT rate from settings"""
    vat_setting = session.exec(
        select(CompanySetting).where(CompanySetting.key == "vat_rate")
    ).first()
    
    if vat_setting:
        try:
            return float(vat_setting.value)
        except:
            return 19.0  # Default fallback
    return 19.0

# Usage in balance calculation
vat_rate = get_vat_rate(session)
vat_amount = total_net * (vat_rate / 100)
total_with_vat = total_net + vat_amount
```

### Example Calculation

**Project Balance with 19% VAT:**
```python
Material costs: 5,000 RON
Labor costs: 3,000 RON
Extra costs: 1,000 RON
----------------------------
Total net: 9,000 RON
VAT (19%): 1,710 RON
----------------------------
Total with VAT: 10,710 RON
```

**Same Project with 9% VAT:**
```python
Total net: 9,000 RON
VAT (9%): 810 RON
----------------------------
Total with VAT: 9,810 RON
```

## Multi-Rate VAT Support

### Future Enhancement

For businesses that need multiple VAT rates:

**Scenario:** Some materials at 19%, others at 9%

**Implementation Plan:**
1. Add `vat_rate` field to Material model
2. Allow per-material VAT rate override
3. Use material-specific rate if set, otherwise use global setting
4. Update balance calculation to sum by VAT rate

**Enhanced Balance Response:**
```json
{
    "total_net": 9000.00,
    "vat_breakdown": [
        {
            "rate": 19.0,
            "base_amount": 8000.00,
            "vat_amount": 1520.00
        },
        {
            "rate": 9.0,
            "base_amount": 1000.00,
            "vat_amount": 90.00
        }
    ],
    "total_vat": 1610.00,
    "total_with_vat": 10610.00
}
```

## Multi-Company VAT

When multi-company support is implemented (see `MULTI_COMPANY_SPEC.md`):

### Per-Company VAT Rates

Each company can have its own VAT rate:

**Company A (Romanian):**
- VAT rate: 19%

**Company B (Bulgarian subsidiary):**
- VAT rate: 20%

**Company C (Special regime):**
- VAT rate: 9%

### Implementation

```python
class CompanySetting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")  # NEW
    key: str
    value: str
    description: Optional[str]
    
    # Unique per company
    class Config:
        unique_together = [["company_id", "key"]]
```

**Query VAT for specific company:**
```python
def get_vat_rate(session: Session, company_id: int) -> float:
    vat_setting = session.exec(
        select(CompanySetting)
        .where(CompanySetting.company_id == company_id)
        .where(CompanySetting.key == "vat_rate")
    ).first()
    
    return float(vat_setting.value) if vat_setting else 19.0
```

## Validation

### Input Validation

VAT rate should be validated:

```python
def validate_vat_rate(value: str) -> bool:
    try:
        rate = float(value)
        return 0 <= rate <= 100
    except:
        return False
```

**Valid values:**
- 0 (VAT exempt)
- 5 (super-reduced)
- 9 (reduced)
- 19 (standard)
- 20 (other EU countries)
- etc.

**Invalid values:**
- Negative numbers
- Values > 100
- Non-numeric strings

### Error Handling

```python
try:
    vat_rate = get_vat_rate(session)
except Exception as e:
    logger.error(f"Failed to get VAT rate: {e}")
    vat_rate = 19.0  # Safe default
```

## Historical VAT Rates

### Tracking Changes

For audit and historical accuracy, consider logging VAT rate changes:

```python
class VATRateHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    old_rate: float
    new_rate: float
    changed_by: int = Field(foreign_key="user.id")
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str]
```

**Use Case:** Recalculate old project balances with historical VAT rates.

## API Endpoints

### Get VAT Rate

```
GET /api/settings/vat_rate
Authorization: Bearer TOKEN

Response:
{
    "key": "vat_rate",
    "value": "19",
    "description": "VAT rate percentage"
}
```

### Update VAT Rate

```
POST /api/settings/
Authorization: Bearer TOKEN
Content-Type: application/json

{
    "key": "vat_rate",
    "value": "9",
    "description": "Reduced VAT rate"
}

Response:
{
    "key": "vat_rate",
    "value": "9",
    "description": "Reduced VAT rate",
    "id": 1,
    "updated_at": "2024-01-15T11:30:00"
}
```

### Get All Settings

```
GET /api/settings/
Authorization: Bearer TOKEN

Response:
[
    {
        "key": "vat_rate",
        "value": "19",
        "description": "VAT rate percentage"
    },
    {
        "key": "company_name",
        "value": "Solar Energy SRL",
        "description": "Company name"
    }
]
```

## Best Practices

### 1. Regular Review

Review VAT rate periodically as tax regulations change.

### 2. Documentation

Document when and why VAT rate changed:
```json
{
    "key": "vat_rate",
    "value": "9",
    "description": "Reduced VAT rate - applicable to solar panels per Law 123/2024"
}
```

### 3. Testing

Test balance calculations after VAT rate changes:
```python
def test_vat_calculation():
    set_vat_rate(19)
    balance = calculate_balance(project_id=1)
    assert balance.vat_rate == 19
    assert balance.vat_amount == balance.total_net * 0.19
```

### 4. User Communication

Notify users when VAT rate changes:
- Email notification
- In-app announcement
- Change log

### 5. Backup Before Change

```bash
# Backup database before changing VAT rate
sqlite3 /opt/pvapp/data/pvapp.db ".backup '/opt/pvapp/backups/before_vat_change.db'"
```

## Troubleshooting

### Issue: VAT Rate Not Applied

**Symptoms:** Balance shows incorrect VAT calculation

**Solutions:**
1. Check setting exists:
   ```sql
   SELECT * FROM company_setting WHERE key = 'vat_rate';
   ```

2. Verify value is numeric:
   ```python
   float(vat_setting.value)  # Should not raise exception
   ```

3. Restart application to reload settings

### Issue: Cannot Update VAT Rate

**Symptoms:** API returns error when updating

**Solutions:**
1. Check admin permissions
2. Verify setting key is correct: `"vat_rate"`
3. Ensure value is valid (0-100)

## Conclusion

VAT configuration is flexible and easy to manage:
- ✅ Stored in database settings
- ✅ Configurable via API or UI
- ✅ Used in balance calculations
- ✅ Support for multiple rates (future)
- ✅ Per-company rates (with multi-company)

**Current Status:**
- Single global VAT rate: ✅ Implemented
- UI configuration: ✅ Implemented
- Multi-rate support: 📋 Planned
- Per-company rates: 📋 Planned (with multi-company)

For questions or issues, refer to the main documentation or contact support.
