# PVApp Backend - stable minimal version

Minimal FastAPI backend with:
- models: Material, Purchase, PurchaseItem, StockMovement (SQLModel)
- endpoints: list/create/detail purchases
- automatic stock movements on purchase creation

Setup
1. Create venv and install:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Initialize DB and run:
   export PVAPP_DB_URL="sqlite:///./db.sqlite3"
   python -c "from app.database import init_db; init_db()"
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

3. Test:
   curl -sS http://127.0.0.1:8000/api/v1/purchases/ | jq .
   See OpenAPI at: http://127.0.0.1:8000/docs

## Upload facturi XML (e-Factura UBL)

Aplicația suportă upload automat de facturi în format XML (e-Factura RO standard UBL).

**Endpoint:** `POST /api/v1/purchases/upload-xml`

**Exemplu curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/purchases/upload-xml" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@factura.xml"
```

Funcționalități:
- Parsare automată facturi UBL XML
- Extragere automată produse, cantități, prețuri
- Creare automată materiale noi dacă nu există
- Actualizare automată stoc

License: MIT
