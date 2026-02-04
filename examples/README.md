# Example Invoice Files

This directory contains sample invoice files for testing the invoice upload feature.

## Files

### 1. sample_invoice_ro.txt
- **Format**: Plain text
- **Language**: Romanian
- **Items**: 6 line items
- **Total**: 19,890.85 RON
- **Content**: 
  - Solar panels
  - Inverters
  - Cables and connectors
  - Mounting structures
  - Distribution box

### 2. sample_invoice_en.txt
- **Format**: Plain text
- **Language**: English
- **Items**: 8 line items
- **Total**: 17,879.75 EUR
- **Content**:
  - Solar panels 400W
  - Hybrid inverter
  - Cables and switches
  - Mounting components

### 3. sample_invoice.xml
- **Format**: XML (e-factura compatible)
- **Language**: Romanian
- **Items**: 6 line items
- **Total**: 33,409.25 RON
- **Features**:
  - Complete XML structure
  - VAT breakdown
  - Supplier/customer details
  - Power optimizers
  - Complete distribution board

## How to Use

### Testing Upload Feature

1. Start the application
2. Login as admin or authorized user
3. Navigate to **Invoices** section
4. Click **📤 Upload Invoice**
5. Select one of these example files
6. Review the extracted data
7. Validate and confirm

### Expected Results

#### sample_invoice_ro.txt
Should extract:
- Supplier: SOLAR ENERGY SRL
- Invoice #: FAC-2024-001
- Date: 15.01.2024
- 6 items with quantities and prices
- Suggested matches for common items

#### sample_invoice_en.txt
Should extract:
- Supplier: GREEN POWER SYSTEMS LTD
- Invoice #: INV-2024-042
- Date: January 20, 2024
- 8 items with detailed descriptions
- Various mounting components

#### sample_invoice.xml
Should extract:
- Supplier: RENEWABLE TECH SRL
- Invoice #: XML-2024-015
- Date: 2024-01-25
- 6 items with complete details
- VAT breakdown
- All items with quantities

## Creating Your Own Test Files

### TXT Format
Use simple tables with:
- Clear headers (Invoice Number, Date, Supplier)
- Column alignment for items
- Quantity, Unit, Price, Total columns
- Clear total section

### XML Format
Use structured tags:
- `<InvoiceNumber>`, `<InvoiceDate>`
- `<Supplier>`, `<Customer>`
- `<LineItems>` with `<Item>` elements
- `<Description>`, `<Quantity>`, `<UnitPrice>`, `<TotalPrice>`
- `<Summary>` with totals

### Tips for Best Results

1. **Consistent formatting**: Use tables or clear structure
2. **Clear labels**: "Invoice Number", "Date", "Supplier"
3. **Item details**: Description, quantity, unit, prices
4. **Total clearly marked**: Label it "TOTAL" or "Total"
5. **Use standard units**: pcs, buc, m, kg, l, etc.

## Troubleshooting

### No Items Extracted
- Check that items are in table format
- Ensure quantities and prices are numbers
- Verify column alignment

### Wrong Supplier/Number
- Make sure these are clearly labeled
- Use standard labels: "Supplier:", "Invoice #:"
- Check that values are on same or next line

### Poor Matching
- Use descriptive item names
- Include power ratings, sizes
- Use consistent terminology

## Adding More Examples

To add more example files:

1. Create new file in this directory
2. Name it descriptively (e.g., `sample_inverter_supplier.txt`)
3. Follow the format patterns shown here
4. Test with upload feature
5. Document expected results in this README

## File Size Guidelines

- **TXT**: Usually < 10KB
- **XML**: Usually < 50KB
- **PDF**: Usually < 500KB (not included in examples)
- **Maximum**: 10MB per file

## Notes

These are fictional invoices for testing purposes only. They represent typical PV installation material invoices but with made-up companies and data.

Real invoices may have:
- Different layouts
- Additional fields
- Multiple currencies
- Tax calculations
- Shipping information
- Payment terms
- Legal disclaimers

The parser is designed to be flexible and extract key information regardless of exact format.
