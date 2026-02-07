# PVApp Backend - stable minimal version

Minimal FastAPI backend with:
- models: Material, Purchase, PurchaseItem, StockMovement (SQLModel)
- endpoints: list/create/detail purchases, XML invoice upload
- automatic stock movements on purchase creation
- XML invoice parsing via microservice integration

## Setup

### 1. Main Backend Setup

Create venv and install:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Initialize DB and run:
```bash
export PVAPP_DB_URL="sqlite:///./db.sqlite3"
python -c "from app.database import init_db; init_db()"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. XML Parser Microservice Setup (Optional)

The XML parser microservice enables robust parsing of UBL XML invoice files using defusedxml to prevent XXE attacks.

#### Local Development with Docker

Build and run the parser service:
```bash
cd services/xml_parser
docker build -t xml-parser .
docker run -p 5000:5000 -e PORT=5000 -e XML_PARSER_TOKEN=your-secret-token xml-parser
```

#### Local Development without Docker

```bash
cd services/xml_parser
pip install -r requirements.txt
export PORT=5000
export XML_PARSER_TOKEN=your-secret-token  # Optional
python parser_app.py
```

#### Test the Parser

Run unit tests:
```bash
cd services/xml_parser
pytest tests/test_parser.py -v
```

Test with a sample XML file:
```bash
python test_local_parse.py tests/sample_invoice.xml
```

#### Configure Backend to Use Parser

Set environment variables in your `.env` file or export them:
```bash
export XML_PARSER_URL=http://localhost:5000
export XML_PARSER_TOKEN=your-secret-token  # Optional, must match parser token
```

### 3. Test the Complete System

Upload an XML invoice:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/invoices/upload \
  -F "file=@services/xml_parser/tests/sample_invoice.xml"
```

List purchases:
```bash
curl -sS http://127.0.0.1:8000/api/v1/purchases/ | jq .
```

OpenAPI documentation: http://127.0.0.1:8000/docs

## Security Notes

- **XXE Protection**: The XML parser uses `defusedxml` to prevent XML External Entity (XXE) attacks
- **Authentication**: Use `XML_PARSER_TOKEN` for inter-service authentication in production
- **HTTPS**: Always use HTTPS for the parser service in production
- **Timeouts**: Parser requests timeout after 30 seconds by default (configurable via `XML_PARSER_TIMEOUT`)

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│  FastAPI        │         │  XML Parser          │
│  Backend        │────────>│  Microservice        │
│  (Port 8000)    │  HTTP   │  (Flask, Port 5000)  │
└─────────────────┘         └──────────────────────┘
       │                              │
       │                              │
       v                              v
  ┌─────────┐                  ┌──────────┐
  │ SQLite  │                  │defusedxml│
  │   DB    │                  │  parser  │
  └─────────┘                  └──────────┘
```

## XML Invoice Upload Flow

1. Client uploads XML invoice to `/api/v1/invoices/upload`
2. Backend detects XML file (by extension or MIME type)
3. Backend sends XML to parser microservice
4. Parser extracts invoice metadata and line items using namespace-aware traversal
5. Backend creates Purchase and PurchaseItem records from parsed data
6. Response includes purchase ID and summary

## License

MIT
