#!/bin/bash
#
# PV Management App - Raspberry Pi Installation Script
# This script automates the installation and setup on Raspberry Pi
#
# Usage: sudo ./install_raspberry_pi.sh
#

set -e  # Exit on error

echo "=================================="
echo "PV Management App - Raspberry Pi"
echo "Automated Installation Script"
echo "=================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Get the actual user who ran sudo
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

# Configuration
INSTALL_DIR="/opt/pvapp"
DATA_DIR="$INSTALL_DIR/data"
BACKUP_DIR="$INSTALL_DIR/backups"
SERVICE_NAME="pvapp"

echo "Configuration:"
echo "  Install Directory: $INSTALL_DIR"
echo "  Data Directory: $DATA_DIR"
echo "  User: $ACTUAL_USER"
echo ""

read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

echo ""
echo "Step 1: Updating system packages..."
apt update
apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
apt install -y python3 python3-pip python3-venv git sqlite3 \
    python3-dev libffi-dev libssl-dev curl

echo ""
echo "Step 3: Checking installation directory..."

# Check if directory exists and handle accordingly
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Git repository already exists. Updating..."
    cd "$INSTALL_DIR"
    sudo -u $ACTUAL_USER git pull
elif [ -d "$INSTALL_DIR" ] && [ "$(ls -A $INSTALL_DIR 2>/dev/null)" ]; then
    # Directory exists and is not empty, but no git repo
    echo ""
    echo "WARNING: $INSTALL_DIR already exists and is not empty."
    echo "This may be from a previous failed installation."
    echo ""
    echo "Options:"
    echo "  1) Remove existing directory and do fresh install (recommended)"
    echo "  2) Cancel installation"
    echo ""
    read -p "Enter your choice (1 or 2): " CHOICE
    
    if [ "$CHOICE" = "1" ]; then
        echo "Removing existing directory..."
        rm -rf "$INSTALL_DIR"
        echo "Directory removed."
    else
        echo "Installation cancelled by user."
        exit 1
    fi
fi

# Create directories (will only create if they don't exist)
echo "Creating installation directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$BACKUP_DIR"

# Clone repository if not already present
if [ ! -d "$INSTALL_DIR/.git" ]; then
    echo ""
    echo "Step 4: Cloning repository..."
    read -p "Enter repository URL (or press Enter for default): " REPO_URL
    if [ -z "$REPO_URL" ]; then
        REPO_URL="https://github.com/catar13274/pvapp-backend-stable.git"
    fi
    
    cd /opt
    sudo -u $ACTUAL_USER git clone "$REPO_URL" pvapp
    cd "$INSTALL_DIR"
else
    cd "$INSTALL_DIR"
fi

echo ""
echo "Step 5: Creating Python virtual environment..."
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    sudo -u $ACTUAL_USER python3 -m venv "$INSTALL_DIR/.venv"
fi

echo ""
echo "Step 6: Installing Python dependencies..."
sudo -u $ACTUAL_USER "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
sudo -u $ACTUAL_USER "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo ""
echo "Step 7: Configuring application..."

# Generate secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Ask for admin password
echo ""
read -p "Enter admin password (or press Enter for auto-generated): " ADMIN_PASSWORD
if [ -z "$ADMIN_PASSWORD" ]; then
    ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    echo "Generated admin password: $ADMIN_PASSWORD"
    echo "IMPORTANT: Save this password!"
fi

# Create .env file
cat > "$INSTALL_DIR/.env" << EOF
# Database URL
PVAPP_DB_URL=sqlite:///$DATA_DIR/db.sqlite3

# Security settings
SECRET_KEY=$SECRET_KEY
ADMIN_PASSWORD=$ADMIN_PASSWORD

# CORS settings (allow all for local network access)
CORS_ORIGINS=*
EOF

chown $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"

echo ""
echo "Step 8: Initializing database..."
cd "$INSTALL_DIR"
export PVAPP_DB_URL="sqlite:///$DATA_DIR/db.sqlite3"
export SECRET_KEY="$SECRET_KEY"
export ADMIN_PASSWORD="$ADMIN_PASSWORD"
sudo -u $ACTUAL_USER -E "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/scripts/init_db.py"

echo ""
echo "Step 9: Creating systemd service..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=PV Management App
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/.venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Step 10: Creating backup script..."
cat > "$INSTALL_DIR/backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/pvapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
if [ -f /opt/pvapp/data/db.sqlite3 ]; then
    cp /opt/pvapp/data/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3
    echo "Backup completed: $BACKUP_DIR/db_$DATE.sqlite3"
    
    # Keep only last 30 days of backups
    find $BACKUP_DIR -name "db_*.sqlite3" -mtime +30 -delete
else
    echo "Database file not found!"
    exit 1
fi
EOF

chmod +x "$INSTALL_DIR/backup.sh"
chown $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR/backup.sh"

echo ""
echo "Step 11: Creating update script..."
cat > "$INSTALL_DIR/update.sh" << 'EOF'
#!/bin/bash
echo "Stopping service..."
sudo systemctl stop pvapp

echo "Creating backup..."
/opt/pvapp/backup.sh

echo "Updating code..."
cd /opt/pvapp
git pull

echo "Updating dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

echo "Starting service..."
sudo systemctl start pvapp

echo "Update completed!"
sudo systemctl status pvapp
EOF

chmod +x "$INSTALL_DIR/update.sh"
chown $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR/update.sh"

echo ""
echo "Step 12: Setting up automatic backup (daily at 2 AM)..."
(sudo -u $ACTUAL_USER crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh >> $INSTALL_DIR/backup.log 2>&1") | sudo -u $ACTUAL_USER crontab -

echo ""
echo "Step 13: Enabling and starting service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Wait a moment for service to start
sleep 3

echo ""
echo "Step 14: Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✓ Service is running!"
else
    echo "✗ Service failed to start. Checking logs..."
    journalctl -u $SERVICE_NAME -n 20
    exit 1
fi

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo "=================================="
echo "Installation Complete! ✓"
echo "=================================="
echo ""
echo "Access Information:"
echo "  Web Interface: http://$IP_ADDRESS:8000"
echo "  API Docs: http://$IP_ADDRESS:8000/docs"
echo ""
echo "Admin Credentials:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Service Management:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Maintenance:"
echo "  Backup:  $INSTALL_DIR/backup.sh"
echo "  Update:  $INSTALL_DIR/update.sh"
echo ""
echo "Configuration:"
echo "  Edit:    sudo nano $INSTALL_DIR/.env"
echo ""
echo "For more information, see:"
echo "  $INSTALL_DIR/RASPBERRY_PI.md"
echo ""
echo "=================================="

# Save credentials to file for reference
cat > "$INSTALL_DIR/CREDENTIALS.txt" << EOF
PV Management App - Installation Info
======================================

Installation Date: $(date)
Raspberry Pi: $(hostname)
IP Address: $IP_ADDRESS

Access URLs:
  Web Interface: http://$IP_ADDRESS:8000
  API Documentation: http://$IP_ADDRESS:8000/docs

Admin Credentials:
  Username: admin
  Password: $ADMIN_PASSWORD

IMPORTANT: Keep this file secure and delete it after noting the password!
EOF

chown $ACTUAL_USER:$ACTUAL_USER "$INSTALL_DIR/CREDENTIALS.txt"
chmod 600 "$INSTALL_DIR/CREDENTIALS.txt"

echo "Installation details saved to: $INSTALL_DIR/CREDENTIALS.txt"
echo ""
