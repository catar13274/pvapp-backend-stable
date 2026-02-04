# E-Factura.ro Integration Guide

## About E-Factura.ro

E-Factura.ro is the Romanian government's mandatory e-invoicing system. All B2B and B2G invoices in Romania must be issued through this platform.

## XML Format

E-Factura.ro uses UBL 2.1 (Universal Business Language) format with Romanian-specific customizations.

### Standard UBL Namespaces

```xml
xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
```

### Romanian Specific Elements

#### Supplier Information
```xml
<cac:AccountingSupplierParty>
    <cac:Party>
        <cac:PartyName>
            <cbc:Name>COMPANY SRL</cbc:Name>
        </cac:PartyName>
        <cac:PostalAddress>
            <cbc:StreetName>Street Name</cbc:StreetName>
            <cbc:CityName>Bucharest</cbc:CityName>
            <cac:Country>
                <cbc:IdentificationCode>RO</cbc:IdentificationCode>
            </cac:Country>
        </cac:PostalAddress>
        <cac:PartyTaxScheme>
            <cbc:CompanyID>RO12345678</cbc:CompanyID>
            <cac:TaxScheme>
                <cbc:ID>VAT</cbc:ID>
            </cac:TaxScheme>
        </cac:PartyTaxScheme>
    </cac:Party>
</cac:AccountingSupplierParty>
```

#### Invoice Header
```xml
<cbc:ID>FA-2024-0001</cbc:ID>
<cbc:IssueDate>2024-01-15</cbc:IssueDate>
<cbc:DueDate>2024-02-15</cbc:DueDate>
<cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
<cbc:DocumentCurrencyCode>RON</cbc:DocumentCurrencyCode>
```

#### Monetary Totals
```xml
<cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="RON">10000.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="RON">10000.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="RON">11900.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="RON">11900.00</cbc:PayableAmount>
</cac:LegalMonetaryTotal>
```

#### Tax Summary
```xml
<cac:TaxTotal>
    <cbc:TaxAmount currencyID="RON">1900.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
        <cbc:TaxableAmount currencyID="RON">10000.00</cbc:TaxableAmount>
        <cbc:TaxAmount currencyID="RON">1900.00</cbc:TaxAmount>
        <cac:TaxCategory>
            <cbc:ID>S</cbc:ID>
            <cbc:Percent>19</cbc:Percent>
            <cac:TaxScheme>
                <cbc:ID>VAT</cbc:ID>
            </cac:TaxScheme>
        </cac:TaxCategory>
    </cac:TaxSubtotal>
</cac:TaxTotal>
```

#### Line Items
```xml
<cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="RON">1000.00</cbc:LineExtensionAmount>
    <cac:Item>
        <cbc:Description>Panou solar 300W</cbc:Description>
        <cbc:Name>Panou solar</cbc:Name>
        <cac:SellersItemIdentification>
            <cbc:ID>PS-300W</cbc:ID>
        </cac:SellersItemIdentification>
        <cac:ClassifiedTaxCategory>
            <cbc:ID>S</cbc:ID>
            <cbc:Percent>19</cbc:Percent>
            <cac:TaxScheme>
                <cbc:ID>VAT</cbc:ID>
            </cac:TaxScheme>
        </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
        <cbc:PriceAmount currencyID="RON">100.00</cbc:PriceAmount>
    </cac:Price>
</cac:InvoiceLine>
```

## Common Issues

### Issue 1: Date Not Detected
**Problem:** `<cbc:IssueDate>` not found  
**Solution:** Check for both `IssueDate` and romanian variants

### Issue 2: Total Not Detected
**Problem:** Multiple total fields in UBL  
**Solution:** Try in order:
1. `PayableAmount` (total with VAT)
2. `TaxInclusiveAmount` (total with VAT)
3. `TaxExclusiveAmount` (total without VAT)
4. `LineExtensionAmount` (sum of lines)

### Issue 3: Garbled Line Items
**Problem:** Description concatenated with quantity/unit  
**Solution:** Parse each field separately:
- Description: `cac:Item/cbc:Description` or `cac:Item/cbc:Name`
- Quantity: `cbc:InvoicedQuantity` text + `@unitCode` attribute
- Price: `cac:Price/cbc:PriceAmount`
- Total: `cbc:LineExtensionAmount`

## Unit Codes (Romanian)

Common unit codes in E-Factura.ro:
- `EA` - Each (bucata - buc)
- `KGM` - Kilogram (kg)
- `MTR` - Meter (metru - m)
- `LTR` - Liter (litru - l)
- `HUR` - Hour (ora - h)
- `SET` - Set
- `BX` - Box (cutie)

## Integration Phases

### Phase 1: Manual Upload (Current)
- [x] User downloads XML from E-Factura.ro
- [x] User uploads via web interface
- [x] System parses and extracts data
- [x] User validates materials
- [x] System creates invoice and stock movements

### Phase 2: API Integration (Future)
- [ ] Configure E-Factura.ro API credentials
- [ ] Implement OAuth authentication
- [ ] Fetch invoices automatically
- [ ] Filter by date range, supplier, status
- [ ] Handle webhook notifications
- [ ] Auto-process invoices

## API Integration (Future)

E-Factura.ro provides REST API for:
- Listing invoices
- Downloading invoice XML
- Updating invoice status
- Sending invoices

Documentation: https://www.anaf.ro/anaf/internet/ANAF/servicii_online/e_factura

### Authentication
E-Factura.ro uses OAuth 2.0:
1. Register application
2. Get client_id and client_secret
3. Implement OAuth flow
4. Store access/refresh tokens

### Endpoints
- List invoices: `GET /PlatformManagedInvoiceV2/list`
- Download: `GET /PlatformManagedInvoiceV2/xml/{downloadId}`
- Upload: `POST /PlatformManagedInvoiceV2/upload`

## Testing

Test files available in `examples/`:
- `sample_invoice.xml` - Standard UBL format
- Real E-Factura.ro XMLs should follow same structure

## Troubleshooting

### Problem: Date/Total Not Extracted
- Check namespace declarations
- Verify XPath expressions
- Check for BOM in XML file
- Validate XML structure

### Problem: Garbled Items
- Check if description merged with other fields
- Verify quantity has separate unitCode attribute
- Check for multi-line descriptions

### Problem: Empty XML Error
- File saved with BOM (use utf-8-sig encoding)
- File not fully written
- Invalid XML structure

## Support

For E-Factura.ro specific issues:
- Official docs: https://www.anaf.ro/anaf/internet/ANAF/servicii_online/e_factura
- Technical support: contact@anaf.ro
- Phone: 021.9434 (Romania)

## Updates

Last updated: 2026-02-04
