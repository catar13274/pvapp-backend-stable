# XML Invoice Parser Microservice

Robust Flask-based XML invoice parser using `defusedxml` to parse UBL XML invoices safely and extract structured data.

## Features

- **Security**: Uses `defusedxml` to prevent XXE (XML External Entity) attacks
- **Robust Parsing**: Avoids fragile XPath predicates by using fully-qualified namespace tags and iterative traversal
- **Flexible Input**: Accepts multipart file upload or raw XML POST
- **Multiple Formats**: Returns JSON (default) or CSV
- **Authentication**: Optional Bearer token authentication
- **UBL Support**: Parses UBL 2.1 invoice format

## Installation

### With Docker (Recommended)

```bash
docker build -t xml-parser .
docker run -p 5000:5000 -e PORT=5000 -e XML_PARSER_TOKEN=your-secret-token xml-parser
```

### Without Docker

```bash
pip install -r requirements.txt
export PORT=5000
export XML_PARSER_TOKEN=your-secret-token  # Optional
python parser_app.py
```

## Usage

### Health Check

```bash
curl http://localhost:5000/health
```

### Parse XML Invoice (Multipart Upload)

```bash
curl -X POST http://localhost:5000/parse \
  -F "file=@tests/sample_invoice.xml" \
  -H "Authorization: Bearer your-secret-token"
```

### Parse XML Invoice (Raw XML)

```bash
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer your-secret-token" \
  --data-binary @tests/sample_invoice.xml
```

### Get CSV Output

```bash
curl -X POST http://localhost:5000/parse?format=csv \
  -F "file=@tests/sample_invoice.xml"
```

## Response Format (JSON)

```json
{
  "success": true,
  "filename": "invoice.xml",
  "data": {
    "invoice_metadata": {
      "invoice_number": "INV-2024-001",
      "invoice_date": "2024-01-15",
      "supplier": "Test Supplier Ltd",
      "total_amount": 1190.0
    },
    "line_items": [
      {
        "line_id": "1",
        "description": "Widget A",
        "sku_raw": "SKU-001",
        "quantity": 10.0,
        "unit_code": "EA",
        "unit_price": 50.0,
        "line_total": 500.0,
        "tax_percent": 19.0,
        "total_price": 500.0
      }
    ]
  }
}
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `5000` | Port to listen on |
| `XML_PARSER_TOKEN` | No | None | Bearer token for authentication |

## Testing

### Run Unit Tests

```bash
pytest tests/test_parser.py -v
```

### Test Locally

```bash
python test_local_parse.py tests/sample_invoice.xml
```

## Supported UBL Elements

The parser extracts the following elements from UBL 2.1 invoices:

### Invoice Metadata
- Invoice number (`cbc:ID`)
- Issue date (`cbc:IssueDate`)
- Supplier name (`cac:AccountingSupplierParty//cbc:Name`)
- Total amount (`cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount` or `PayableAmount`)

### Line Items
- Line ID
- Item description/name
- Seller item identification (SKU)
- Quantity and unit code
- Unit price
- Line extension amount (total before tax)
- Tax percentage
- Calculated total price

## Security Notes

1. **XXE Protection**: Uses `defusedxml.ElementTree` which is hardened against XXE attacks
2. **Authentication**: Set `XML_PARSER_TOKEN` environment variable and include `Authorization: Bearer <token>` header
3. **Production**: Use HTTPS in production deployments
4. **Timeouts**: Client should implement request timeouts (recommended: 30-60 seconds)

## Architecture

The parser uses:
- **Flask** for HTTP server
- **defusedxml** for safe XML parsing
- **Gunicorn** for production WSGI server (2 workers, 60s timeout)

Parsing approach:
- Fully-qualified namespace tags (expanded QNames)
- Iterative traversal with `findall()` instead of complex XPath predicates
- Graceful handling of missing or malformed elements
- Comprehensive logging for debugging

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Invalid XML or missing file |
| 401 | Authentication failed |
| 500 | Internal server error |

## License

MIT
