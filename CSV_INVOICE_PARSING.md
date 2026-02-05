# CSV Invoice Parsing Guide

## Overview

This guide explains how to use the CSV invoice parsing feature, which provides deterministic, rule-based invoice parsing without AI or external services.

## Features

- ✅ **Flexible CSV Parsing** - Auto-detect or configure column mapping
- ✅ **Fuzzy Material Matching** - Match items against your material database
- ✅ **Romanian Support** - Handles Romanian formats and terminology
- ✅ **No External Dependencies** - Uses Python standard library only
- ✅ **Confidence Scores** - Know how reliable each match is
- ✅ **Free & Private** - No API costs, data stays local

## Quick Start

### 1. Prepare Your CSV

Create a CSV file with invoice data. Example (`invoice.csv`):

```csv
Cod,Denumire,Cant,PretUnit,Total
MAT-001,Panou solar 300W,20,450.00,9000.00
MAT-002,Inverter 5kW,2,1500.00,3000.00
MAT-003,Cablu solar 6mm,100,5.50,550.00
```

### 2. Upload and Parse

**Basic upload (auto-detect columns):**
```bash
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@invoice.csv"
```

**With custom column mapping:**
```bash
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@invoice.csv" \
  -F 'mapping={"sku":"Cod","description":"Denumire","quantity":"Cant","unit_price":"PretUnit","total_price":"Total"}'
```

### 3. Review Results

The API returns:
- Parsed invoice data
- Material matches with confidence scores
- Detected column mapping
- Total calculations

## Supported Column Names

The parser auto-detects these column patterns:

### SKU / Code
- English: `sku`, `code`, `item_code`, `material_code`
- Romanian: `cod`

### Description
- English: `description`, `name`, `product`
- Romanian: `denumire`, `nume`, `produs`

### Quantity
- English: `quantity`, `qty`
- Romanian: `cantitate`, `cant`, `cant.`

### Unit
- English: `unit`
- Romanian: `um`, `u.m.`, `unitate`

### Unit Price
- English: `unit_price`, `price`
- Romanian: `pret`, `pret_unitar`, `pretunit`, `pret_unit`

### Total Price
- English: `total`, `total_price`, `sum`
- Romanian: `suma`, `valoare`

## CSV Format Requirements

### Minimum Requirements
- **Headers**: First row must contain column names
- **Description**: Required for each item
- **Quantity**: Required for each item (numbers only)

### Optional Fields
- SKU/Code
- Unit of measure
- Unit price
- Total price

### Delimiters
- Comma (`,`) - Default
- Semicolon (`;`) - Auto-detected for Romanian files

### Decimal Separators
- Dot (`.`) - Standard: `123.45`
- Comma (`,`) - Romanian: `123,45` (automatically converted)

## Material Matching

### How It Works

The system matches invoice items to your material database using two methods:

#### 1. SKU Exact Match
- Compares invoice SKU with material SKU
- Confidence: 1.0 (100%)
- Match type: `sku_exact`

#### 2. Description Fuzzy Match
- Uses Python's difflib for similarity matching
- Compares normalized strings (lowercase, no extra spaces)
- Confidence: 0.0-1.0 (calculated by difflib)
- Match type: `description_fuzzy`
- Default cutoff: 0.6 (60% similarity)

### Match Response Format

```json
{
  "material_id": 123,
  "material_name": "Solar Panel 300W",
  "material_sku": "MAT-001",
  "confidence": 0.95,
  "match_type": "description_fuzzy"
}
```

### Interpreting Confidence Scores

- **1.0**: Perfect match (exact SKU)
- **0.9-0.99**: Excellent match (very similar description)
- **0.8-0.89**: Good match (similar description)
- **0.7-0.79**: Fair match (review recommended)
- **0.6-0.69**: Weak match (manual review needed)
- **<0.6**: No match returned

## API Reference

### Endpoint: Parse CSV Invoice

**POST** `/api/v1/purchases/parse/csv`

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | CSV file upload |
| mapping | JSON String | No | Custom column mapping |
| match_materials | Boolean | No | Enable fuzzy matching (default: true) |

#### Column Mapping Format

```json
{
  "sku": "Your_SKU_Column_Name",
  "description": "Your_Description_Column_Name",
  "quantity": "Your_Quantity_Column_Name",
  "unit": "Your_Unit_Column_Name",
  "unit_price": "Your_Price_Column_Name",
  "total_price": "Your_Total_Column_Name"
}
```

#### Response Format

```json
{
  "success": true,
  "supplier": null,
  "invoice_number": null,
  "invoice_date": null,
  "total_amount": 15150.00,
  "items_count": 5,
  "items": [
    {
      "sku": "MAT-001",
      "description": "Panou solar 300W",
      "quantity": 20.0,
      "unit": "buc",
      "unit_price": 450.00,
      "total_price": 9000.00,
      "material_match": {
        "material_id": 1,
        "material_name": "Solar Panel 300W",
        "material_sku": "MAT-001",
        "confidence": 0.95,
        "match_type": "description_fuzzy"
      }
    }
  ],
  "detected_columns": ["sku", "description", "quantity", "unit_price", "total_price"],
  "column_mapping": {
    "sku": "Cod",
    "description": "Denumire",
    "quantity": "Cant",
    "unit_price": "PretUnit",
    "total_price": "Total"
  }
}
```

## Usage Examples

### Example 1: Romanian Invoice

**CSV File (`factura_ro.csv`):**
```csv
Cod;Denumire;Cant;UM;PretUnit;Total
SP-300;Panou solar 300W;20;buc;450,00;9000,00
INV-5K;Inverter 5kW;2;buc;1500,00;3000,00
```

**Command:**
```bash
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@factura_ro.csv"
```

**Result:**
- Automatically detects semicolon delimiter
- Converts comma decimals to dots
- Matches materials by description

### Example 2: English Invoice with Custom Mapping

**CSV File (`invoice_en.csv`):**
```csv
Item Code,Product Name,Qty,Unit,Price Each,Line Total
SOL-300W,Solar Panel 300W,20,pcs,450.00,9000.00
INV-5KW,Inverter 5kW,2,pcs,1500.00,3000.00
```

**Command:**
```bash
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@invoice_en.csv" \
  -F 'mapping={"sku":"Item Code","description":"Product Name","quantity":"Qty","unit":"Unit","unit_price":"Price Each","total_price":"Line Total"}'
```

### Example 3: Parse Without Matching

**Command:**
```bash
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@invoice.csv" \
  -F "match_materials=false"
```

**Result:**
- Parses CSV data only
- No material matching performed
- Faster processing
- Useful for validation or import

## Integration Workflow

### Recommended Flow

1. **Parse CSV** → Get structured data with material matches
2. **Review Matches** → Check confidence scores
3. **Manual Adjustment** → Override low-confidence matches
4. **Create Purchase** → Use `/api/v1/purchases/` endpoint
5. **Update Stock** → Automatic via purchase creation

### Complete Example

```bash
# Step 1: Parse CSV
curl -X POST http://localhost:8000/api/v1/purchases/parse/csv \
  -F "file=@invoice.csv" \
  > parsed_result.json

# Step 2: Review and adjust matches in parsed_result.json

# Step 3: Create purchase with matched materials
curl -X POST http://localhost:8000/api/v1/purchases/ \
  -H "Content-Type: application/json" \
  -d @purchase_payload.json
```

## Troubleshooting

### Problem: No columns detected

**Cause**: CSV has no headers or unrecognized format

**Solution**: 
- Ensure first row contains column names
- Use custom column mapping
- Check file encoding (should be UTF-8)

### Problem: Decimal parsing errors

**Cause**: Mixed decimal separators

**Solution**:
- Use consistent decimal separator (`.` or `,`)
- Parser auto-converts Romanian commas to dots
- Check for thousands separators (not supported)

### Problem: Low match confidence

**Cause**: Description differences between invoice and database

**Solution**:
- Improve material descriptions in database
- Adjust cutoff threshold in code
- Use SKU matching when possible
- Manual review and override

### Problem: Delimiter not detected

**Cause**: File uses unusual delimiter

**Solution**:
- Manually specify delimiter in code
- Convert file to standard CSV format
- Use custom parsing logic

## Performance

### Speed
- **Small files** (<100 items): < 1 second
- **Medium files** (100-1000 items): 1-5 seconds
- **Large files** (1000+ items): 5-30 seconds

### Limits
- Maximum file size: 10MB (configurable)
- Maximum items: 10,000 (recommended)
- Material DB size: Affects fuzzy matching speed

## Best Practices

### CSV Preparation
1. ✅ Include clear headers in first row
2. ✅ Use consistent column names
3. ✅ Ensure required fields (description, quantity)
4. ✅ Use standard delimiters (comma or semicolon)
5. ✅ UTF-8 encoding
6. ✅ Clean data (no empty rows)

### Material Database
1. ✅ Maintain accurate SKUs
2. ✅ Use descriptive material names
3. ✅ Consistent naming conventions
4. ✅ Regular database cleanup
5. ✅ Avoid duplicates

### Matching
1. ✅ Review low-confidence matches (< 0.8)
2. ✅ Use SKU matching when available
3. ✅ Update material descriptions based on patterns
4. ✅ Build supplier-specific templates over time

## Advanced Configuration

### Adjust Fuzzy Matching Cutoff

Edit `app/invoice_parser.py`:

```python
# Default cutoff is 0.6 (60% similarity)
match = match_material_fuzzy(
    description=item['description'],
    sku=item.get('sku'),
    materials=materials_list,
    cutoff=0.7  # Increase for stricter matching
)
```

### Add Custom Column Patterns

Edit `default_mapping` in `parse_csv()`:

```python
default_mapping = {
    'sku': ['sku', 'cod', 'code', 'your_custom_sku_name'],
    'description': ['description', 'your_custom_desc_name'],
    # ...
}
```

### Per-Supplier Templates

Create YAML configuration files:

```yaml
# supplier_templates.yml
ROMSTAL:
  columns:
    sku: "Cod produs"
    description: "Denumire"
    quantity: "Cantitate"
  patterns:
    invoice_number: "FS-.*"
```

## Future Enhancements

Planned features:
- [ ] Per-supplier template configuration (YAML/JSON)
- [ ] Enhanced text invoice parsing (non-CSV)
- [ ] Validation rules per field type
- [ ] Unit tests with fixture CSV files
- [ ] Direct CSV import to purchases
- [ ] Batch processing multiple files
- [ ] Web UI for CSV upload
- [ ] Match history and learning

## Support

For issues or questions:
1. Check this documentation
2. Review example CSV files in `examples/`
3. Check API logs for error details
4. Verify material database has items to match against

## Related Documentation

- [Invoice Upload Guide](INVOICE_UPLOAD.md)
- [Purchase API Reference](app/api/purchases.py)
- [Parser Implementation](app/invoice_parser.py)
