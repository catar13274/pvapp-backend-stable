#!/bin/bash
#
# PV Management App - Uninstallation Script
# Removes the application from Raspberry Pi / Linux system
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/pvapp"
SERVICE_NAME="pvapp"
DATA_DIR="/opt/pvapp/data"
BACKUP_DIR="/opt/pvapp/backups"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}PV Management App - Uninstallation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if application is installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}PV Management App is not installed at $INSTALL_DIR${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

echo -e "${YELLOW}WARNING: This will remove the PV Management App from your system.${NC}"
echo ""
echo "The following will be removed:"
echo "  • Application directory: $INSTALL_DIR"
echo "  • Systemd service: $SERVICE_NAME"
echo "  • Service configuration"
echo ""
echo -e "${YELLOW}Your data will be KEPT by default (database and backups).${NC}"
echo "You will be asked if you want to remove the data."
echo ""

# Confirmation
read -p "Are you sure you want to uninstall? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1: Stopping service...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    echo "✓ Service stopped"
else
    echo "Service is not running"
fi

echo ""
echo -e "${BLUE}Step 2: Disabling service...${NC}"
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl disable "$SERVICE_NAME"
    echo "✓ Service disabled"
else
    echo "Service was not enabled"
fi

echo ""
echo -e "${BLUE}Step 3: Removing systemd service file...${NC}"
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    echo "✓ Service file removed"
else
    echo "Service file not found"
fi

echo ""
echo -e "${BLUE}Step 4: Backing up data (optional)...${NC}"
if [ -d "$DATA_DIR" ] && [ "$(ls -A $DATA_DIR)" ]; then
    read -p "Do you want to backup your data before removal? (yes/no): " BACKUP_DATA
    if [ "$BACKUP_DATA" = "yes" ]; then
        BACKUP_LOCATION="$HOME/pvapp-backup-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_LOCATION"
        
        echo "Creating backup at: $BACKUP_LOCATION"
        
        if [ -d "$DATA_DIR" ]; then
            cp -r "$DATA_DIR" "$BACKUP_LOCATION/"
            echo "✓ Data backed up"
        fi
        
        if [ -d "$BACKUP_DIR" ]; then
            cp -r "$BACKUP_DIR" "$BACKUP_LOCATION/"
            echo "✓ Backups backed up"
        fi
        
        echo ""
        echo -e "${GREEN}Backup created at: $BACKUP_LOCATION${NC}"
        echo "You can restore this data later if needed."
    fi
fi

echo ""
echo -e "${BLUE}Step 5: Removing data (optional)...${NC}"
read -p "Do you want to PERMANENTLY DELETE the database and all data? (yes/no): " DELETE_DATA
if [ "$DELETE_DATA" = "yes" ]; then
    read -p "Are you ABSOLUTELY SURE? This CANNOT be undone! (yes/no): " CONFIRM_DELETE
    if [ "$CONFIRM_DELETE" = "yes" ]; then
        if [ -d "$DATA_DIR" ]; then
            rm -rf "$DATA_DIR"
            echo "✓ Data directory removed"
        fi
        
        if [ -d "$BACKUP_DIR" ]; then
            rm -rf "$BACKUP_DIR"
            echo "✓ Backup directory removed"
        fi
        echo -e "${RED}All data has been permanently deleted.${NC}"
    else
        echo "Data deletion cancelled. Data preserved."
    fi
else
    echo "Data preserved. You can find it at:"
    echo "  Database: $DATA_DIR/pvapp.db"
    echo "  Backups: $BACKUP_DIR/"
    echo ""
    echo "To restore later, copy these directories to the new installation."
fi

echo ""
echo -e "${BLUE}Step 6: Removing application directory...${NC}"
# Remove everything except data directory if it was preserved
if [ -d "$DATA_DIR" ] || [ -d "$BACKUP_DIR" ]; then
    # Data was preserved, remove only application files
    echo "Removing application files (preserving data)..."
    
    # Remove specific directories
    rm -rf "$INSTALL_DIR/.venv" 2>/dev/null || true
    rm -rf "$INSTALL_DIR/app" 2>/dev/null || true
    rm -rf "$INSTALL_DIR/frontend" 2>/dev/null || true
    rm -rf "$INSTALL_DIR/scripts" 2>/dev/null || true
    rm -rf "$INSTALL_DIR/examples" 2>/dev/null || true
    
    # Remove files
    rm -f "$INSTALL_DIR"/*.py 2>/dev/null || true
    rm -f "$INSTALL_DIR"/*.txt 2>/dev/null || true
    rm -f "$INSTALL_DIR"/*.md 2>/dev/null || true
    rm -f "$INSTALL_DIR"/*.sh 2>/dev/null || true
    rm -f "$INSTALL_DIR"/.env 2>/dev/null || true
    rm -f "$INSTALL_DIR"/.git* 2>/dev/null || true
    
    echo "✓ Application files removed"
    echo ""
    echo -e "${GREEN}Data preserved at: $INSTALL_DIR${NC}"
    echo "To completely remove, manually delete: sudo rm -rf $INSTALL_DIR"
else
    # Data was deleted or didn't exist, remove entire directory
    rm -rf "$INSTALL_DIR"
    echo "✓ Complete installation directory removed"
fi

echo ""
echo -e "${BLUE}Step 7: Removing update script (if exists)...${NC}"
if [ -f "$INSTALL_DIR/update.sh" ]; then
    rm -f "$INSTALL_DIR/update.sh"
    echo "✓ Update script removed"
else
    echo "Update script not found"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "PV Management App has been removed from your system."
echo ""

if [ -d "$DATA_DIR" ] || [ -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Note: Your data has been preserved.${NC}"
    echo "Location: $INSTALL_DIR"
    echo ""
    echo "To reinstall and use this data:"
    echo "  1. Run the installation script"
    echo "  2. Copy the data directory to the new installation"
    echo ""
fi

if [ -n "$BACKUP_LOCATION" ] && [ -d "$BACKUP_LOCATION" ]; then
    echo -e "${GREEN}Your data backup is available at:${NC}"
    echo "$BACKUP_LOCATION"
    echo ""
fi

echo "Thank you for using PV Management App!"
echo ""
