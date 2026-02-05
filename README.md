# PVApp Backend

Multi-company materials management system with eFactura.ro integration, Make.com webhooks, and Llama 3 AI assistant.

## Features

- 🏢 **Multi-company support** - Manage multiple companies in one system
- 📦 **Materials management** - Track inventory, stock levels, and movements
- 🧾 **Purchase management** - Handle invoices and purchase orders
- 🤖 **AI Assistant** - Llama 3 integration for intelligent data extraction
- 🔗 **Make.com webhooks** - Automation platform integration
- 📊 **eFactura.ro integration** - Romanian e-invoice system support
- 🔐 **Authentication** - User management with role-based access

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases with Python type hints
- **Llama 3** - AI-powered assistant via llama-cpp-python
- **Make.com** - No-code automation platform integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/catar13274/pvapp-backend-stable.git
cd pvapp-backend-stable
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export DATABASE_URL="sqlite:///./pvapp.db"
export LLAMA_MODEL_PATH="./models/llama-3-8b.gguf"
```

## Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/users` - List users
- `PUT /auth/users/{user_id}` - Update user

### Companies
- `GET /companies/` - List companies
- `GET /companies/{company_id}` - Get company
- `POST /companies/` - Create company
- `PUT /companies/{company_id}` - Update company
- `DELETE /companies/{company_id}` - Delete company

### Materials
- `GET /materials/` - List materials
- `GET /materials/{material_id}` - Get material
- `POST /materials/` - Create material
- `PUT /materials/{material_id}` - Update material
- `DELETE /materials/{material_id}` - Delete material
- `POST /materials/{material_id}/stock/adjust` - Adjust stock
- `GET /materials/{material_id}/movements` - Get stock movements
- `GET /materials/company/{company_id}/low-stock` - Get low stock items

### Purchases
- `GET /purchases/` - List purchases
- `GET /purchases/{purchase_id}` - Get purchase
- `POST /purchases/` - Create purchase
- `GET /purchases/{purchase_id}/items` - Get purchase items
- `POST /purchases/{purchase_id}/items` - Add purchase item

### Make.com Webhooks
- `POST /webhooks/make/invoice` - Receive invoice from Make.com
- `POST /webhooks/make/material-update` - Receive material update
- `POST /webhooks/make/stock-alert` - Receive stock alert
- `GET /webhooks/make/logs/{company_id}` - Get webhook logs

## Database Models

### Company
- Multi-tenant support
- Company settings and configuration

### User
- Authentication and authorization
- Role-based access (admin/user)

### Material
- SKU, name, description
- Current stock, minimum stock
- Unit of measurement

### Purchase
- Invoice number, date
- Supplier information
- Total amount

### PurchaseItem
- Line items for purchases
- Quantity, unit price
- Link to materials

### StockMovement
- Track all stock changes
- Movement type (purchase, sale, adjustment)
- Audit trail

### WebhookLog
- Log all webhook events
- Status tracking
- Error handling

## AI Integration

### Llama 3 Assistant Features

1. **Invoice Data Extraction**
```python
from app.integrations.llama import LlamaAssistant

assistant = LlamaAssistant()
data = assistant.extract_invoice_data(invoice_text)
```

2. **Material SKU Matching**
```python
material_id = assistant.match_material_sku(description, existing_materials)
```

3. **Stock Reorder Suggestions**
```python
suggestion = assistant.suggest_stock_reorder(material_data, usage_history)
```

## Make.com Integration

Connect your Make.com scenarios to these webhook endpoints:

1. **Invoice Processing**: Send invoice data to `/webhooks/make/invoice`
2. **Material Updates**: Update materials via `/webhooks/make/material-update`
3. **Stock Alerts**: Receive alerts at `/webhooks/make/stock-alert`

## Development

### Project Structure
```
pvapp-backend-stable/
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── companies.py
│   │   ├── materials.py
│   │   ├── purchases.py
│   │   └── make_webhooks.py
│   ├── integrations/
│   │   └── llama.py
│   ├── models.py
│   ├── database.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.