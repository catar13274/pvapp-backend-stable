#!/bin/bash
# Update script for PV Management App
# Pulls latest code, installs dependencies, runs migrations, and restarts service

set -e  # Exit on error

echo "================================"
echo "PV Management App - Update"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Detect installation directory
if [ -d "/opt/pvapp" ]; then
    INSTALL_DIR="/opt/pvapp"
else
    echo "Error: Installation directory not found at /opt/pvapp"
    exit 1
fi

cd "$INSTALL_DIR"

echo "Step 1: Stopping service..."
if systemctl is-active --quiet pvapp; then
    systemctl stop pvapp
    echo "✓ Service stopped"
else
    echo "⚠ Service not running"
fi

echo ""
echo "Step 2: Pulling latest code..."
sudo -u $(stat -c '%U' .) git pull
if [ $? -eq 0 ]; then
    echo "✓ Code updated"
else
    echo "✗ Git pull failed"
    exit 1
fi

echo ""
echo "Step 3: Installing/updating dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies updated"
else
    echo "✗ Dependency installation failed"
    exit 1
fi

echo ""
echo "Step 4: Running database migrations..."
python scripts/migrate_db.py
if [ $? -eq 0 ]; then
    echo "✓ Migrations completed"
else
    echo "⚠ Migration had issues (might be OK if already migrated)"
fi

echo ""
echo "Step 5: Starting service..."
systemctl start pvapp
if [ $? -eq 0 ]; then
    echo "✓ Service started"
else
    echo "✗ Service start failed"
    exit 1
fi

echo ""
echo "Step 6: Checking service status..."
sleep 2
if systemctl is-active --quiet pvapp; then
    echo "✓ Service is running"
else
    echo "✗ Service failed to start"
    echo ""
    echo "Check logs with: sudo journalctl -u pvapp -n 50"
    exit 1
fi

echo ""
echo "================================"
echo "Update completed successfully!"
echo "================================"
echo ""
echo "Service status:"
systemctl status pvapp --no-pager -l
echo ""
echo "Access your application at: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
