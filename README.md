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

## Upload facturi XML (e-Factura UBL)

Aplicația suportă upload automat de facturi în format XML (e-Factura RO standard UBL).

**Endpoint:** `POST /api/invoices/upload`

**Exemplu curl:**
```bash
curl -X POST "http://localhost:8000/api/invoices/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@factura.xml"
```

Funcționalități:
- Parsare automată facturi UBL XML via microservice
- Extragere automată produse, cantități, prețuri
- Creare automată înregistrări Purchase și PurchaseItem
- Protecție împotriva atacurilor XXE (defusedxml)


License: MIT
Initialize DB and run:
```bash
export PVAPP_DB_URL="sqlite:///./db.sqlite3"
python -c "from app.database import init_db; init_db()"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. XML Parser Microservice Setup (Optional)

The XML parser microservice enables robust parsing of UBL XML invoice files using defusedxml to prevent XXE attacks.

#### Production Setup with systemd

For production deployments, run the XML parser as a systemd service:

1. **Create a dedicated service user (recommended for security):**
```bash
sudo useradd -r -s /bin/false pvapp
sudo chown -R pvapp:pvapp /opt/pvapp
```

2. **Install the service file:**
```bash
sudo cp pvapp-xml-parser.service /etc/systemd/system/
sudo systemctl daemon-reload
```

3. **Configure environment variables:**
Add to your `.env` file:
```bash
XML_PARSER_URL=http://localhost:5000
XML_PARSER_TOKEN=my-secret-token
```

Note: The service binds to `127.0.0.1:5000` for local-only access, enhancing security.

4. **Start and enable the service:**
```bash
sudo systemctl enable pvapp-xml-parser
sudo systemctl start pvapp-xml-parser
```

5. **Check service status:**
```bash
sudo systemctl status pvapp-xml-parser
sudo journalctl -u pvapp-xml-parser -f
```

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
curl -X POST http://127.0.0.1:8000/api/invoices/upload \
  -F "file=@services/xml_parser/tests/sample_invoice.xml"
```

List purchases:
```bash
curl -sS http://127.0.0.1:8000/api/v1/purchases/ | jq .
```

OpenAPI documentation: http://127.0.0.1:8000/docs

## Updating the Application

Use the provided update script to pull changes and restart services:
```bash
./update.sh
```

This will:
- Pull latest changes from git
- Update dependencies for both backend and XML parser
- Restart the pvapp service (if running)
- Restart the pvapp-xml-parser service (if running)

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

1. Client uploads XML invoice to `/api/invoices/upload`
2. Backend detects XML file (by extension or MIME type)
3. Backend sends XML to parser microservice
4. Parser extracts invoice metadata and line items using namespace-aware traversal
5. Backend creates Purchase and PurchaseItem records from parsed data
6. Response includes purchase ID and summary

## License

MIT
