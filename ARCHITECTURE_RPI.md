# PV Management App - Raspberry Pi Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         LOCAL NETWORK                            │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Laptop     │   │   Phone      │   │   Tablet     │       │
│  │              │   │              │   │              │       │
│  │  Browser     │   │  Browser     │   │  Browser     │       │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             │                                    │
│                    WiFi / Ethernet                               │
│                             │                                    │
│         ┌───────────────────▼───────────────────┐               │
│         │      Raspberry Pi (192.168.1.100)     │               │
│         │                                        │               │
│         │  ┌──────────────────────────────────┐ │               │
│         │  │   PV Management App              │ │               │
│         │  │                                  │ │               │
│         │  │  ┌────────────┐  ┌────────────┐ │ │               │
│         │  │  │  Frontend  │  │  FastAPI   │ │ │               │
│         │  │  │  (HTML/CSS)│──│  Backend   │ │ │               │
│         │  │  │  /JS)      │  │            │ │ │               │
│         │  │  └────────────┘  └──────┬─────┘ │ │               │
│         │  │                          │       │ │               │
│         │  │                   ┌──────▼─────┐ │ │               │
│         │  │                   │  SQLite DB │ │ │               │
│         │  │                   │ /opt/pvapp │ │ │               │
│         │  │                   │   /data/   │ │ │               │
│         │  │                   └────────────┘ │ │               │
│         │  └──────────────────────────────────┘ │               │
│         │                                        │               │
│         │  Port 8000 (HTTP)                     │               │
│         │  Auto-start via systemd               │               │
│         │  Daily backups at 2 AM                │               │
│         └────────────────────────────────────────┘               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Installation Flow

```
┌────────────┐
│   Start    │
└─────┬──────┘
      │
      ▼
┌─────────────────────────┐
│ Run Installation Script │
└─────┬───────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Install Dependencies     │
│ - Python 3              │
│ - pip, venv, git        │
│ - SQLite                │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Clone Repository         │
│ to /opt/pvapp           │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Create Virtual Env       │
│ Install Python packages  │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Generate Secure Config   │
│ - SECRET_KEY            │
│ - ADMIN_PASSWORD        │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Initialize Database      │
│ Create admin user        │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Create Systemd Service   │
│ Enable auto-start        │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Setup Backup Scripts     │
│ Configure cron job       │
└─────┬────────────────────┘
      │
      ▼
┌──────────────────────────┐
│ Start Service            │
└─────┬────────────────────┘
      │
      ▼
┌─────────────┐
│   Running!  │
│  Access at: │
│  http://IP  │
│    :8000    │
└─────────────┘
```

## Directory Structure on Raspberry Pi

```
/opt/pvapp/
├── .venv/                    # Python virtual environment
├── app/                      # Application code
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── auth.py              # Authentication
│   └── api/                 # API endpoints
│       ├── auth.py
│       ├── materials.py
│       ├── projects.py
│       ├── stock.py
│       ├── costs.py
│       ├── balance.py
│       ├── settings.py
│       └── invoices.py
├── frontend/                 # Web interface
│   ├── index.html           # Main page
│   ├── style.css            # Styles
│   └── app.js               # Frontend logic
├── scripts/                  # Utility scripts
│   └── init_db.py           # DB initialization
├── data/                     # Database directory
│   ├── db.sqlite3           # Main database
│   └── db.sqlite3-journal   # SQLite journal
├── backups/                  # Automatic backups
│   ├── db_20260204_020000.sqlite3
│   ├── db_20260203_020000.sqlite3
│   └── ...
├── .env                      # Configuration (secure)
├── backup.sh                 # Backup script
├── update.sh                 # Update script
├── requirements.txt          # Python dependencies
└── RASPBERRY_PI.md          # Documentation

/etc/systemd/system/
└── pvapp.service            # Systemd service config

/var/log/journal/
└── pvapp logs               # Service logs (via journald)
```

## System Resource Usage

```
Raspberry Pi Model    | Recommended Config  | Memory Usage | CPU Usage
---------------------|---------------------|--------------|----------
Pi 3B (1GB)          | 1 worker           | ~200-300MB   | 30-50%
Pi 3B+ (1GB)         | 1 worker           | ~200-300MB   | 25-45%
Pi 4 (2GB)           | 2 workers          | ~300-500MB   | 20-40%
Pi 4 (4GB)           | 3-4 workers        | ~400-700MB   | 15-30%
Pi 5 (4GB+)          | 3-4 workers        | ~400-700MB   | 10-25%
```

## Network Topology

```
Internet
    │
    │ (Optional)
    │
┌───▼──────────────────┐
│  Router              │
│  192.168.1.1         │
└───┬──────────────────┘
    │
    │ Local Network (192.168.1.0/24)
    │
    ├─── PC (192.168.1.10)
    │
    ├─── Phone (192.168.1.20)
    │
    ├─── Tablet (192.168.1.30)
    │
    └─── Raspberry Pi (192.168.1.100)
         │
         └─── PV Management App
              Port 8000
```

## Service Lifecycle

```
Boot
  │
  ▼
┌────────────────┐
│ System Startup │
└───────┬────────┘
        │
        ▼
┌────────────────────┐
│ Network Ready      │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Start pvapp.service│
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Load .env config   │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Start Uvicorn      │
│ with 2 workers     │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ App Running        │
│ Serving on :8000   │
└───────┬────────────┘
        │
        │ (If crash)
        ▼
┌────────────────────┐
│ Auto-restart       │
│ (after 10 sec)     │
└───────┬────────────┘
        │
        └──────► Back to "Start Uvicorn"
```

## Data Flow

```
User Browser
    │
    │ HTTP Request
    ▼
FastAPI
    │
    ├─── GET /api/materials
    │    │
    │    ▼
    │  SQLModel ORM
    │    │
    │    ▼
    │  SQLite DB
    │    │
    │    ▼
    │  JSON Response
    │
    ├─── POST /api/stock/movement
    │    │
    │    ▼
    │  Validate Data
    │    │
    │    ▼
    │  Update Stock
    │    │
    │    ▼
    │  SQLite DB
    │    │
    │    ▼
    │  Success Response
    │
    └─── GET /api/balance/1/pdf
         │
         ▼
       Calculate Balance
         │
         ▼
       Generate PDF
       (ReportLab)
         │
         ▼
       Download PDF
```

## Backup Strategy

```
Daily Cron Job (2:00 AM)
    │
    ▼
┌────────────────────┐
│ backup.sh runs     │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Copy db.sqlite3    │
│ to backups/        │
│ with timestamp     │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Delete backups     │
│ older than 30 days │
└────────────────────┘

Manual Backup:
  $ /opt/pvapp/backup.sh

Restore:
  1. Stop service
  2. Copy backup to data/db.sqlite3
  3. Start service
```

## Update Process

```
User runs: /opt/pvapp/update.sh
    │
    ▼
┌────────────────────┐
│ Stop Service       │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Create Backup      │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Git Pull           │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Update Dependencies│
│ (pip install)      │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Start Service      │
└───────┬────────────┘
        │
        ▼
┌────────────────────┐
│ Check Status       │
└────────────────────┘
```

## Security Model

```
External Network
    │
    │ (Blocked by router/firewall)
    │
┌───▼──────────────────┐
│  Router/Firewall     │
└───┬──────────────────┘
    │
    │ Local Network Only
    │
┌───▼──────────────────┐
│  Raspberry Pi        │
│                      │
│  Port 8000 (HTTP)    │
│  ↓                   │
│  FastAPI             │
│  ↓                   │
│  JWT Authentication  │
│  - SECRET_KEY        │
│  - bcrypt passwords  │
│  - Role-based access │
│  ↓                   │
│  SQLite Database     │
│  (File permissions)  │
└──────────────────────┘
```

---

For detailed setup instructions, see:
- **English**: RASPBERRY_PI.md
- **Română**: INSTALARE_ROMANA.md
- **Quick Ref**: QUICKSTART_RPI.md
