#!/usr/bin/env bash
# update.sh - Update and restart PVApp services

set -euo pipefail

echo "=== PVApp Update Script ==="
echo ""

# Change to the script's directory
cd "$(dirname "$0")"

# Update main backend
echo "1. Pulling latest changes from git..."
git pull

echo ""
echo "2. Installing/updating backend dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt

# Install XML parser dependencies if the service exists
if [ -d "services/xml_parser" ]; then
    echo ""
    echo "3. Installing/updating XML parser dependencies..."
    pip install -q -r services/xml_parser/requirements.txt
fi

# Restart main backend service if it exists
if systemctl is-active --quiet pvapp 2>/dev/null; then
    echo ""
    echo "4. Restarting main backend service..."
    sudo systemctl restart pvapp
    echo "   Main backend service restarted"
else
    echo ""
    echo "4. Main backend service not found (pvapp)"
    echo "   To enable: sudo systemctl enable pvapp"
    echo "   To start: sudo systemctl start pvapp"
fi

# Restart XML parser service if it exists
if systemctl is-active --quiet pvapp-xml-parser 2>/dev/null; then
    echo ""
    echo "5. Restarting XML parser service..."
    sudo systemctl restart pvapp-xml-parser
    echo "   XML parser service restarted"
elif [ -f "pvapp-xml-parser.service" ]; then
    echo ""
    echo "5. XML parser service not active (pvapp-xml-parser)"
    echo "   To install: sudo cp pvapp-xml-parser.service /etc/systemd/system/"
    echo "   To enable: sudo systemctl enable pvapp-xml-parser"
    echo "   To start: sudo systemctl start pvapp-xml-parser"
fi

echo ""
echo "=== Update complete ==="
echo ""
echo "Check service status:"
echo "  sudo systemctl status pvapp"
echo "  sudo systemctl status pvapp-xml-parser"
echo ""
echo "View logs:"
echo "  sudo journalctl -u pvapp -f"
echo "  sudo journalctl -u pvapp-xml-parser -f"
