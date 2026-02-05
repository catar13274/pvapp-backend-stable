# ROMSTAL Invoice Parsing Solution

## Problem Summary

The invoice parser was extracting incorrect items from ROMSTAL invoices:
- Bank account numbers (CONT: RO53 INGB, CONT: RO58 CITI)
- Garbage text ("RONbuc")
- Missing actual products
- Special character prefixes (++, --, @@) in descriptions

## Solution Implemented

Complete rewrite of the `extract_line_items()` function in `app/invoice_parser.py` with comprehensive filtering and pattern matching.

### Key Enhancements

#### 1. Line Filtering
Skip non-product lines that should not be extracted:
- Bank information (BANCA:, CONT RON:)
- Company details (C.I.F., Sediul, Capital social)
- Headers (Furnizor:, Cumparator:)
- Footer information (Semnatura, Date privind, GESTIUNEA)
- Total lines

#### 2. Strict Product Line Matching
Requires lines to follow ROMSTAL format:
```
<line_number> <SKU> <description> <unit> <qty> <unit_price> <total>
```

Example:
```
1 35FV1598 +Invertor monofazat Goodwe, GW5000-ES-20, 5 kW - P2 buc 1,000 3.179,84 3.179,84
```

#### 3. Description Cleaning
- Remove leading special characters: +, -, @, *, #, &
- Remove trailing special characters
- Clean up multiple spaces
- Remove "RON" currency symbols from descriptions

#### 4. SKU Integration
Combine SKU code with description:
```
35FV1598 - Invertor monofazat Goodwe, GW5000-ES-20, 5 kW
```

#### 5. Proper Unit Extraction
Extract unit from pattern match:
- buc (bucăți/pieces)
- kg (kilogram)
- m (metru/meter)
- l (litru/liter)
- h (oră/hour)
- set
- pcs

#### 6. Romanian Number Format
Handle Romanian number format correctly:
- Input: 3.179,84 (thousands separator: dot, decimal: comma)
- Output: 3179.84 (standard decimal format)

## Expected Results

### ROMSTAL Invoice Test Case

**Input:** ROMSTAL invoice with 3 products

**Output:** Exactly 3 extracted items

**Item 1:**
```
SKU: 35FV1598
Description: Invertor monofazat Goodwe, GW5000-ES-20, 5 kW - P2 / taxa verde 25.00
Quantity: 1
Unit: buc
Unit Price: 3,179.84 RON
Total: 3,179.84 RON
```

**Item 2:**
```
SKU: 35FV1667
Description: Modul baterie, Goodwe, Lynx U G3, LV, 5 kWh - P2
Quantity: 2
Unit: buc
Unit Price: 3,643.94 RON
Total: 7,287.88 RON
```

**Item 3:**
```
SKU: 35FV1707
Description: Smart meter, monofazat, GMK110D, AC Couple - M2 / taxa verde 2.00
Quantity: 1
Unit: buc
Unit Price: 289.26 RON
Total: 289.26 RON
```

## Validation Screen Display

After parsing, the validation screen should show:

| Description | Qty | Unit | Unit Price | Total | Action | Material |
|-------------|-----|------|------------|-------|--------|----------|
| 35FV1598 - Invertor monofazat Goodwe, GW5000-ES-20, 5 kW | 1 | buc | 3,179.84 | 3,179.84 | Use Existing | Select Material |
| 35FV1667 - Modul baterie, Goodwe, Lynx U G3, LV, 5 kWh | 2 | buc | 3,643.94 | 7,287.88 | Use Existing | Select Material |
| 35FV1707 - Smart meter, monofazat, GMK110D, AC Couple | 1 | buc | 289.26 | 289.26 | Use Existing | Select Material |

✓ **No bank accounts**
✓ **No "RONbuc" garbage**
✓ **Clean descriptions**
✓ **All products extracted**

## Testing

### Upload ROMSTAL Invoice

```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -F "file=@examples/romstal_invoice_test.txt" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Expected API Response

```json
{
  "id": 1,
  "supplier": "ROMSTAL IMEX SRL",
  "invoice_number": "0854089560",
  "invoice_date": "2025-10-03",
  "total_amount": 13015.95,
  "status": "PARSED",
  "items": [
    {
      "description": "35FV1598 - Invertor monofazat Goodwe, GW5000-ES-20, 5 kW - P2 / taxa verde 25.00",
      "quantity": 1,
      "unit": "buc",
      "unit_price": 3179.84,
      "total_price": 3179.84
    },
    {
      "description": "35FV1667 - Modul baterie, Goodwe, Lynx U G3, LV, 5 kWh - P2",
      "quantity": 2,
      "unit": "buc",
      "unit_price": 3643.94,
      "total_price": 7287.88
    },
    {
      "description": "35FV1707 - Smart meter, monofazat, GMK110D, AC Couple - M2 / taxa verde 2.00",
      "quantity": 1,
      "unit": "buc",
      "unit_price": 289.26,
      "total_price": 289.26
    }
  ]
}
```

## Benefits

✅ **Accurate Extraction** - Only actual products are extracted
✅ **No False Positives** - Bank accounts and headers filtered out
✅ **Clean Data** - Special characters removed, descriptions cleaned
✅ **Complete SKU Support** - Product codes properly integrated
✅ **Romanian Format** - Number format handled correctly
✅ **Proper Units** - Units correctly detected and extracted

## Limitations

- Requires ROMSTAL-specific format (line number + SKU + description)
- May not work for other supplier formats (need additional patterns)
- Relies on consistent table structure
- Text-based parsing (works with extracted text, not scanned images)

## Future Enhancements

1. **Multi-Supplier Support** - Add templates for other Romanian suppliers
2. **Configurable Patterns** - YAML/JSON config for supplier-specific rules
3. **Better OCR Integration** - For scanned invoices
4. **Learning System** - Save corrections for pattern improvement
5. **Confidence Scoring** - Add extraction confidence levels

## Related Files

- `app/invoice_parser.py` - Main parser implementation
- `examples/romstal_invoice_test.txt` - Test invoice file
- `ROMSTAL_INVOICE_ANALYSIS.md` - Detailed analysis
- `CSV_INVOICE_PARSING.md` - CSV alternative approach
