# Multi-Company Architecture Specification

## Overview

This document specifies the architecture for transforming the PV Management App from a single-company application to a multi-company (multi-tenant) system.

**Requirement:** "programul va trebui sa fie multi firma" (the program should be multi-company)

## Current State

**Single Company:**
- All data belongs to one implicit company
- No company identification in database
- No data isolation between companies
- Settings are global

## Target State

**Multi-Company:**
- Multiple companies can use the same instance
- Data completely isolated by company
- Each company has own materials, projects, invoices, etc.
- Settings per company (including VAT rates)
- Users can belong to one or multiple companies

## Database Schema Changes

### New Company Model

```python
class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    fiscal_code: str = Field(unique=True)  # CUI/CIF in Romania
    registration_number: Optional[str]  # Nr. Reg. Com.
    address: Optional[str]
    city: Optional[str]
    country: str = Field(default="Romania")
    phone: Optional[str]
    email: Optional[str]
    bank_account: Optional[str]
    bank_name: Optional[str]
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Tables Requiring company_id

All major tables need to be associated with a company:

1. **User**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```
   
2. **Material**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

3. **MaterialPrice**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

4. **Project**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

5. **StockMovement**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

6. **Invoice**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

7. **InvoiceItem**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

8. **LaborCost**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

9. **ExtraCost**
   ```python
   company_id: int = Field(foreign_key="company.id")
   ```

10. **CompanySetting**
    ```python
    company_id: int = Field(foreign_key="company.id")
    # Each company has own settings (including VAT rate)
    ```

### Indexes

Add composite indexes for performance:
```sql
CREATE INDEX idx_material_company ON material(company_id);
CREATE INDEX idx_project_company ON project(company_id);
CREATE INDEX idx_stockmovement_company ON stockmovement(company_id);
CREATE INDEX idx_invoice_company ON invoice(company_id);
-- etc. for all tables
```

## Authentication Changes

### JWT Token Enhancement

Add company context to JWT tokens:
```python
{
    "sub": "username",
    "user_id": 123,
    "company_id": 5,  # NEW
    "role": "ADMIN",
    "exp": 1234567890
}
```

### Company Selection at Login

**For users with single company:**
- Automatically select that company
- Include in JWT token

**For users with multiple companies:**
- After authentication, show company selector
- User chooses active company
- Issue JWT with selected company_id

### Company Switching

**Without re-login:**
- Endpoint: `POST /api/auth/switch-company`
- Request: `{"company_id": 5}`
- Response: New JWT token with new company_id
- Validates user has access to target company

## API Changes

### Data Isolation

**All queries must filter by company:**
```python
# Before (current)
materials = session.exec(select(Material)).all()

# After (with company isolation)
materials = session.exec(
    select(Material).where(Material.company_id == current_company_id)
).all()
```

### Dependency for Company Context

```python
def get_current_company(token: str = Depends(oauth2_scheme)) -> int:
    """Extract company_id from JWT token"""
    payload = decode_token(token)
    return payload.get("company_id")

# Use in endpoints
@router.get("/materials")
def get_materials(
    company_id: int = Depends(get_current_company),
    session: Session = Depends(get_session)
):
    materials = session.exec(
        select(Material).where(Material.company_id == company_id)
    ).all()
    return materials
```

### Company Management Endpoints

**Admin Only:**

```python
# List companies
GET /api/companies/
Response: [{"id": 1, "name": "Company A", ...}, ...]

# Get company
GET /api/companies/{company_id}
Response: {"id": 1, "name": "Company A", ...}

# Create company
POST /api/companies/
Request: {"name": "New Company", "fiscal_code": "...", ...}
Response: {"id": 5, "name": "New Company", ...}

# Update company
PUT /api/companies/{company_id}
Request: {"name": "Updated Name", ...}

# Delete/Deactivate company
DELETE /api/companies/{company_id}
```

### User-Company Association

```python
# Assign user to company
POST /api/companies/{company_id}/users
Request: {"user_id": 123, "role": "INSTALLER"}

# Remove user from company
DELETE /api/companies/{company_id}/users/{user_id}

# List company users
GET /api/companies/{company_id}/users
```

## UI/UX Changes

### Navigation Bar

Add company selector:
```
┌─────────────────────────────────────────────┐
│ PV App  | [Company A ▼] | User | Logout    │
└─────────────────────────────────────────────┘
```

Dropdown shows:
- Current company (highlighted)
- Other accessible companies
- "Switch to..." action

### Company Management Interface

**Admin only, accessible from Settings:**

```
Companies Management
┌──────────────────────────────────────────────┐
│ + Add Company                                │
│                                              │
│ Company A                [Edit] [Deactivate]│
│ CUI: 12345678                                │
│ Active users: 5                              │
│                                              │
│ Company B                [Edit] [Deactivate]│
│ CUI: 87654321                                │
│ Active users: 3                              │
└──────────────────────────────────────────────┘
```

### Settings Per Company

Each company has independent settings:
- VAT rate (can differ per company)
- Company info (address, bank details)
- Preferences
- etc.

## Migration Strategy

### Phase 1: Create Company Infrastructure

1. **Add Company model**
2. **Create default company** for existing data
3. **Add company_id columns** to all tables (nullable initially)
4. **Set default company** for all existing records
5. **Make company_id non-nullable** after data migration
6. **Add foreign key constraints**

### Phase 2: Update Application Logic

1. **Update authentication** to include company context
2. **Update all queries** to filter by company
3. **Add company management APIs**
4. **Test data isolation**

### Phase 3: UI Integration

1. **Add company selector** to navigation
2. **Add company management interface**
3. **Test company switching**
4. **End-to-end testing**

### Migration Script

```python
# scripts/migrate_to_multicompany.py

def migrate():
    # Create default company
    default_company = Company(
        name="Main Company",
        fiscal_code="DEFAULT",
        is_active=True
    )
    session.add(default_company)
    session.commit()
    
    # Assign all existing data to default company
    session.exec(
        update(User).values(company_id=default_company.id)
    )
    session.exec(
        update(Material).values(company_id=default_company.id)
    )
    # ... repeat for all tables
    
    session.commit()
    print("✓ Migration complete")
```

## Security Considerations

### Row-Level Security

**Critical:** Users must NEVER see data from other companies.

**Implementation:**
- All database queries filter by company_id
- JWT token validates company access
- API middleware enforces company context
- Database triggers prevent cross-company writes

### Access Control

**Admin Privileges:**
- Can manage companies (create, edit, deactivate)
- Can assign users to companies
- Can view all data within their company

**Regular Users:**
- Can only access their assigned company data
- Cannot see or modify other companies
- Cannot switch to unauthorized companies

### Audit Logging

Log all company-related actions:
- Company creation/modification
- User assignment to companies
- Company switching
- Cross-company access attempts (security alert)

## Performance Considerations

### Indexing

**Essential indexes:**
```sql
CREATE INDEX idx_material_company_id ON material(company_id);
CREATE INDEX idx_project_company_id ON project(company_id);
-- etc. for all foreign keys
```

### Query Optimization

**Always use company filter in WHERE clause:**
```sql
-- Good (uses index)
SELECT * FROM material WHERE company_id = 5;

-- Bad (table scan)
SELECT * FROM material;
```

### Connection Pooling

Consider per-company connection pools for large installations.

## Testing Strategy

### Unit Tests

```python
def test_data_isolation():
    # Create two companies
    company1 = create_company("Company A")
    company2 = create_company("Company B")
    
    # Create materials for each
    mat1 = create_material("Material A", company1.id)
    mat2 = create_material("Material B", company2.id)
    
    # Query as company1
    materials = get_materials(company_id=company1.id)
    assert mat1 in materials
    assert mat2 not in materials
    
    # Query as company2
    materials = get_materials(company_id=company2.id)
    assert mat1 not in materials
    assert mat2 in materials
```

### Integration Tests

- Test complete workflows per company
- Test company switching
- Test admin company management
- Test authorization edge cases

### Load Testing

- Multiple companies accessing simultaneously
- Company switching performance
- Query performance with company filters

## Rollback Plan

If issues arise:

1. **Database:** Keep company_id nullable with default
2. **Code:** Feature flag to enable/disable multi-company
3. **Data:** Can revert to single default company
4. **Users:** Maintain backward compatibility

## Implementation Timeline

### Phase 1: Database (1-2 weeks)
- [ ] Create Company model
- [ ] Migration scripts
- [ ] Add company_id to tables
- [ ] Test data migration

### Phase 2: Backend (1 week)
- [ ] Update authentication
- [ ] Add company filtering
- [ ] Company management APIs
- [ ] Unit tests

### Phase 3: Frontend (1 week)
- [ ] Company selector UI
- [ ] Company management interface
- [ ] Company switching
- [ ] Integration tests

**Total: 3-4 weeks** for complete implementation

## Future Enhancements

### Advanced Features

- **Company Groups:** Hierarchical company structures
- **Data Sharing:** Optional cross-company data sharing
- **White Labeling:** Custom branding per company
- **Usage Analytics:** Per-company usage statistics
- **Billing:** Per-company subscription management

## References

- FastAPI Multi-Tenancy: https://fastapi.tiangolo.com/
- SQLModel Documentation: https://sqlmodel.tiangolo.com/
- Multi-Tenant Architecture Patterns: https://docs.microsoft.com/en-us/azure/architecture/patterns/multi-tenancy

## Conclusion

This specification provides a complete blueprint for implementing multi-company support. The phased approach allows for safe, tested implementation while maintaining backward compatibility with existing single-company installations.

**Key Success Criteria:**
- ✅ Complete data isolation between companies
- ✅ Seamless company switching
- ✅ Performance maintained with proper indexing
- ✅ Security enforced at all levels
- ✅ Backward compatible migration
