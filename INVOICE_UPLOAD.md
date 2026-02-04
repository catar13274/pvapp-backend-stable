# Invoice File Upload Feature

## Overview

The PV Management App now supports automatic invoice processing through file upload. Upload invoices in PDF, DOC, TXT, or XML format, and the system will automatically extract materials, suggest matches with existing inventory, and allow you to validate before creating stock entries.

## Supported File Formats

- **PDF** (.pdf) - Most common format
- **DOC/DOCX** (.doc, .docx) - Microsoft Word documents
- **TXT** (.txt) - Plain text files
- **XML** (.xml) - Electronic invoices (e-factura format compatible)

## How It Works

### 1. Upload Invoice

1. Navigate to **Invoices** section
2. Click **📤 Upload Invoice** button
3. Select your invoice file (max 10MB)
4. Click **Upload & Parse**

The system will:
- Upload and save the file securely
- Extract text from the document
- Identify invoice metadata (supplier, number, date, total)
- Extract line items (description, quantity, unit price, total)
- Suggest matching materials from existing inventory

### 2. Validate Materials

After upload, you'll see a validation screen with all extracted items:

**For each item, you can:**

#### Option A: Use Existing Material
- Select from dropdown of existing materials
- System shows confidence score for suggested matches
- Example: "Solar Panel 300W (85% match)"

#### Option B: Create New Material
- Enter material name (auto-filled from invoice description)
- Set category (e.g., "Solar Panels", "Inverters", "Cables")
- Set unit of measurement (pcs, kg, m, etc.)
- Set minimum stock level

### 3. Confirm Invoice

After validation:
1. Click **✓ Validate & Confirm**
2. System creates any new materials
3. Maps all items to materials
4. Optionally confirm invoice immediately
5. Creates IN stock movements
6. Updates material inventory

## Invoice Status Flow

```
UPLOADED → PARSED → VALIDATED → CONFIRMED
```

- **UPLOADED**: File uploaded, awaiting parsing
- **PARSED**: Data extracted, awaiting validation
- **VALIDATED**: Materials mapped, ready to confirm
- **CONFIRMED**: Stock movements created, inventory updated

## What Gets Extracted

### Invoice Header
- Supplier name
- Invoice number
- Invoice date
- Total amount

### Line Items
For each item:
- Description/name
- Quantity
- Unit of measurement
- Unit price
- Total price

## Material Matching

The system uses fuzzy matching to suggest existing materials:

**Matching Algorithm:**
- Compares invoice item descriptions with material names
- Calculates similarity score (0-100%)
- Suggests best matches above 30% confidence
- Shows confidence score to help you decide

**Example:**
```
Invoice: "Panou solar fotovoltaic 300W"
Matches: "Solar Panel 300W" (85% confidence)
```

## Creating New Materials

When creating materials from invoices:

**Required Fields:**
- Name: Material name (auto-filled from invoice)
- Category: Product category
- Unit: Unit of measurement
- Minimum Stock: Threshold for low stock alerts

**Auto-filled Values:**
- Name: From invoice description
- Unit: From invoice (if detected)
- Initial stock: 0 (will be updated on confirmation)

## Best Practices

### File Preparation
1. **Scan quality**: Use high-quality scans for PDFs
2. **File naming**: Use descriptive names (e.g., "Invoice_ABC_2024.pdf")
3. **Format**: PDF works best, followed by TXT
4. **Language**: Works with Romanian and English invoices

### Validation
1. **Review carefully**: Check all extracted items
2. **Use suggestions**: Confidence > 70% is usually accurate
3. **Be consistent**: Use same material names for similar items
4. **Categories**: Keep categories consistent (helps with reports)

### After Upload
1. **Verify totals**: Check if extracted total matches actual invoice
2. **Check quantities**: Ensure quantities are correct
3. **Confirm promptly**: Don't leave invoices in PARSED status
4. **Review stock**: Check that inventory updated correctly

## Troubleshooting

### Issue: No Items Extracted
**Causes:**
- Poor scan quality
- Invoice in unsupported format
- Non-standard invoice layout

**Solutions:**
- Re-scan invoice at higher quality
- Convert to TXT manually and upload
- Enter invoice items manually using View mode

### Issue: Wrong Supplier/Number
**Cause:** Invoice uses non-standard formatting

**Solution:** 
- Continue with validation
- Correct information manually if needed
- System will still extract items correctly

### Issue: Low Match Confidence
**Cause:** Material names differ from invoice descriptions

**Solutions:**
- Review the suggested match carefully
- Use "Create New" if no good match exists
- Consider updating material names for consistency

### Issue: Missing Quantities or Prices
**Cause:** Complex table layouts in invoice

**Solution:**
- Items still created with 0 quantity
- Edit manually after upload
- Or re-upload with better format

## Example Invoice Formats

### Simple TXT Format
```
INVOICE #12345
Date: 2024-01-15
Supplier: ABC Solar SRL

Item                    Qty    Unit Price    Total
Solar Panel 300W        10     500.00        5000.00
Inverter 3kW            2      1500.00       3000.00
Cable 6mm              100     5.00          500.00

TOTAL: 8500.00 RON
```

### XML (e-factura) Format
```xml
<?xml version="1.0"?>
<Invoice>
    <Supplier>ABC Solar SRL</Supplier>
    <InvoiceNumber>12345</InvoiceNumber>
    <InvoiceDate>2024-01-15</InvoiceDate>
    <LineItems>
        <Item>
            <Description>Solar Panel 300W</Description>
            <Quantity>10</Quantity>
            <Unit>pcs</Unit>
            <UnitPrice>500.00</UnitPrice>
            <TotalPrice>5000.00</TotalPrice>
        </Item>
    </LineItems>
    <Total>8500.00</Total>
</Invoice>
```

## API Endpoints

### Upload Invoice
```http
POST /api/invoices/upload
Content-Type: multipart/form-data

file: <invoice_file>
```

**Response:**
```json
{
    "message": "Invoice uploaded and parsed successfully",
    "invoice_id": 123,
    "invoice": {
        "id": 123,
        "supplier": "ABC Solar SRL",
        "invoice_number": "12345",
        "invoice_date": "2024-01-15",
        "total_amount": 8500.00,
        "status": "PARSED"
    },
    "items": [
        {
            "id": 456,
            "description": "Solar Panel 300W",
            "quantity": 10,
            "unit": "pcs",
            "unit_price": 500.00,
            "total_price": 5000.00,
            "suggested_material_id": 78,
            "match_confidence": 0.85
        }
    ],
    "items_count": 3
}
```

### Validate Invoice Items
```http
POST /api/invoices/{invoice_id}/validate-items
Content-Type: application/json

[
    {
        "item_id": 456,
        "material_id": 78,
        "create_new": false
    },
    {
        "item_id": 457,
        "create_new": true,
        "new_material": {
            "name": "Inverter 3kW",
            "category": "Inverters",
            "unit": "pcs",
            "minimum_stock": 2
        }
    }
]
```

**Response:**
```json
{
    "message": "Invoice items validated successfully",
    "invoice_id": 123,
    "created_materials": 1,
    "updated_items": 3,
    "materials": [
        {
            "id": 99,
            "name": "Inverter 3kW",
            "category": "Inverters",
            "unit": "pcs"
        }
    ]
}
```

## Security

- **Authentication Required**: Must be logged in to upload
- **File Type Validation**: Only allowed formats accepted
- **File Size Limit**: 10MB maximum
- **Secure Storage**: Files stored outside web root
- **Unique Filenames**: Prevents conflicts with timestamps
- **Virus Scanning**: Recommended in production (not included)

## Performance

- **Upload Speed**: Depends on file size (usually < 5 seconds)
- **Parsing Time**: 
  - TXT: < 1 second
  - PDF: 1-3 seconds
  - DOC: 2-5 seconds
  - XML: < 1 second
- **Matching**: < 1 second for up to 1000 materials

## Limitations

- **File Size**: Maximum 10MB
- **OCR**: No OCR for scanned images (use PDF with text layer)
- **Complex Layouts**: May struggle with very complex table layouts
- **Languages**: Best with Romanian and English
- **Accuracy**: Depends on invoice format consistency

## Future Enhancements

Potential improvements:
- OCR integration for scanned images
- AI-powered material classification
- Automatic category detection
- Learning from user corrections
- Batch upload multiple invoices
- Email import from suppliers
- Direct integration with supplier APIs

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review example formats
3. Try different file format (PDF → TXT)
4. Contact system administrator

## Tips for Best Results

1. **Standardize with suppliers**: Request invoices in consistent format
2. **Name materials consistently**: Use same names across all invoices
3. **Keep categories simple**: 5-10 categories is optimal
4. **Review weekly**: Don't let parsed invoices accumulate
5. **Train users**: Show team how to validate effectively
