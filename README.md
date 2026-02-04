# PV Management App

Complete full-stack application for PV (Photovoltaic) installation management with:

## 🌟 Perfect for Raspberry Pi!

This application runs perfectly on Raspberry Pi, making it ideal for on-site installation management!

**Quick Raspberry Pi Installation:**
```bash
# Method 1: Direct download (recommended after merge to main)
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/copilot/add-user-registration-endpoint/install_raspberry_pi.sh -o install.sh
sudo bash install.sh

# Method 2: Clone repository
git clone -b copilot/add-user-registration-endpoint https://github.com/catar13274/pvapp-backend-stable.git
cd pvapp-backend-stable
sudo bash install_raspberry_pi.sh
```

📖 **Detailed guides:**
- [English Raspberry Pi Guide](RASPBERRY_PI.md) - Complete deployment guide
- [Ghid în Română](INSTALARE_ROMANA.md) - Ghid complet de instalare

## Frontend Features

- **Modern Web Interface**: Clean, responsive UI built with vanilla JavaScript, HTML, and CSS
- **Authentication**: Secure login with JWT tokens
- **Dashboard**: Overview with key statistics (materials, projects, stock alerts)
- **Materials Management**: Add, view, and manage materials with stock tracking
- **Projects Management**: Create and track PV installation projects
- **Stock Management**: Track IN/OUT stock movements with automatic inventory updates
- **Cost Tracking**: Record labor and extra costs for projects
- **Balance Reports**: View detailed project cost breakdowns with VAT calculations
- **Invoice Upload**: 📤 Upload invoices (PDF, DOC, TXT, XML) with automatic material extraction
- **Company Settings**: Configure VAT rates and other company settings
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Backend Features

- **Authentication**: JWT-based authentication with role-based access (ADMIN, INSTALLER)
- **Materials Management**: CRUD operations, pricing history, stock alerts
- **Projects**: Client projects with system specifications and status tracking
- **Stock Management**: IN/OUT movements with project linking
- **Cost Tracking**: Labor and extra costs per project
- **Balance & Reports**: Complete project balance calculations with PDF export
- **Company Settings**: Configurable settings (VAT rate, etc.)
- **Invoice Processing**: 
  - 📄 Multi-format file upload (PDF, DOC, DOCX, TXT, XML)
  - 🤖 Automatic text extraction and parsing
  - 🎯 Intelligent material matching with confidence scores
  - ✅ User validation workflow
  - 🆕 Auto-creation of new materials
  - 📦 Automatic stock IN movements

## Setup

1. **Create virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize database and create admin user:**
   ```bash
   export PVAPP_DB_URL="sqlite:///./db.sqlite3"
   python scripts/init_db.py
   ```
   
   Default admin credentials:
   - Username: `admin`
   - Password: `admin123`
   - ⚠️ Change password after first login!

3. **Run the server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   
   Or use the provided script:
   ```bash
   ./run.sh
   ```

4. **Access the application:**
   - **Web Interface**: http://127.0.0.1:8000
   - **API Documentation**: http://127.0.0.1:8000/docs
   - **Alternative API Docs**: http://127.0.0.1:8000/redoc
   
   Default login credentials:
   - Username: `admin`
   - Password: From `ADMIN_PASSWORD` env variable or auto-generated

5. **Test the API (optional):**
   ```bash
   # Login to get token
   curl -X POST "http://127.0.0.1:8000/api/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   
   # Access protected endpoints with token
   curl -H "Authorization: Bearer <your-token>" \
     http://127.0.0.1:8000/api/auth/me
   ```
   
   **Interactive API documentation:**
   - Swagger UI: http://127.0.0.1:8000/docs
   - ReDoc: http://127.0.0.1:8000/redoc

## Frontend Structure

```
frontend/
├── index.html    # Main HTML with all views
├── style.css     # Complete styling
└── app.js        # JavaScript for API integration and UI logic
```

The frontend is a Single Page Application (SPA) that:
- Communicates with the backend API
- Stores JWT tokens in localStorage
- Provides modal forms for data entry
- Updates views dynamically without page reloads
- Shows real-time statistics and data

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user (Admin only)
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/users` - List all users (Admin only)

### Materials
- `POST /api/materials/` - Create material
- `GET /api/materials/` - List materials
- `GET /api/materials/{id}` - Get material details
- `PUT /api/materials/{id}` - Update material
- `DELETE /api/materials/{id}` - Delete material
- `POST /api/materials/prices` - Add material price
- `GET /api/materials/{id}/prices` - Get price history
- `GET /api/materials/low-stock/alert` - Get low stock alerts

### Projects
- `POST /api/projects/` - Create project
- `GET /api/projects/` - List projects (with status filter)
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Stock Management
- `POST /api/stock/movement` - Create stock movement (IN/OUT)
- `GET /api/stock/movements` - List movements (with filters)
- `GET /api/stock/movements/{id}` - Get movement details

### Costs
- `POST /api/costs/labor` - Create labor cost
- `GET /api/costs/labor` - List labor costs
- `PUT /api/costs/labor/{id}` - Update labor cost
- `DELETE /api/costs/labor/{id}` - Delete labor cost
- `POST /api/costs/extra` - Create extra cost
- `GET /api/costs/extra` - List extra costs
- `PUT /api/costs/extra/{id}` - Update extra cost
- `DELETE /api/costs/extra/{id}` - Delete extra cost

### Balance & Reports
- `GET /api/balance/{project_id}` - Get project balance
- `GET /api/balance/{project_id}/pdf` - Download balance PDF

### Settings
- `GET /api/settings/` - List all settings
- `POST /api/settings/` - Create/update setting (Admin only)
- `GET /api/settings/{key}` - Get specific setting
- `DELETE /api/settings/{key}` - Delete setting (Admin only)

### Invoices
- `GET /api/invoices/pending` - Get pending invoices
- `GET /api/invoices/{id}` - Get invoice details
- `PUT /api/invoices/{id}/items/{item_id}` - Map item to material
- `POST /api/invoices/{id}/confirm` - Confirm invoice

## Environment Variables

- `PVAPP_DB_URL` - Database URL (default: `sqlite:///./db.sqlite3`)
- `SECRET_KEY` - Secret key for JWT token signing (required for production)
- `ADMIN_PASSWORD` - Initial admin password (if not set, a random password is generated)
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins (default: `*`)

## Development

The application uses:
- **FastAPI** - Modern web framework
- **SQLModel** - SQL database ORM
- **JWT** - Authentication tokens
- **ReportLab** - PDF generation
- **Passlib + Bcrypt** - Password hashing

## License

MIT
