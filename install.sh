#!/usr/bin/env bash
# install.sh - PVApp Backend Installation Script
# This script installs pvapp-backend with all dependencies on Raspberry Pi/Debian-based systems
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/master/install.sh | bash
#   
# Or with custom installation directory:
#   curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/master/install.sh | INSTALL_DIR=/opt/myapp bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${INSTALL_DIR:-/opt/pvapp}"
REPO_URL="https://github.com/catar13274/pvapp-backend-stable.git"
REPO_BRANCH="${REPO_BRANCH:-master}"
PVAPP_USER="pvapp"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  PVApp Backend Installation Script${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_error "This script should not be run as root"
        print_info "Run as a regular user with sudo privileges"
        exit 1
    fi
    
    # Check if user has sudo privileges
    if ! sudo -n true 2>/dev/null; then
        print_warning "This script requires sudo privileges"
        print_info "You may be prompted for your password"
        sudo -v
    fi
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if running on Debian-based OS
    if [ ! -f /etc/debian_version ]; then
        print_error "This script requires a Debian-based OS (Raspberry Pi OS, Ubuntu, Debian, etc.)"
        exit 1
    fi
    print_success "Debian-based OS detected"
    
    # Check for required commands
    local missing_commands=()
    
    if ! command -v apt-get &> /dev/null; then
        missing_commands+=("apt-get")
    fi
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

install_system_dependencies() {
    print_info "Installing system dependencies..."
    
    # Update apt package list
    print_info "Updating apt package list..."
    sudo apt-get update -qq
    print_success "Package list updated"
    
    # Install required packages
    local packages=(git python3 python3-pip python3-venv)
    print_info "Installing: ${packages[*]}"
    
    sudo apt-get install -y -qq "${packages[@]}"
    print_success "System dependencies installed"
}

install_application() {
    print_info "Installing PVApp Backend..."
    
    # Check if installation directory exists
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Installation directory $INSTALL_DIR already exists"
        read -p "Do you want to remove it and reinstall? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -rf "$INSTALL_DIR"
            print_success "Removed existing installation"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Create parent directory if it doesn't exist
    sudo mkdir -p "$(dirname "$INSTALL_DIR")"
    
    # Clone repository
    print_info "Cloning repository from $REPO_URL..."
    sudo git clone -b "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
    print_success "Repository cloned to $INSTALL_DIR"
    
    # Change to installation directory
    cd "$INSTALL_DIR"
    
    # Create Python virtual environment
    print_info "Creating Python virtual environment..."
    sudo python3 -m venv .venv
    print_success "Virtual environment created"
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    sudo .venv/bin/pip install -q --upgrade pip
    sudo .venv/bin/pip install -q -r requirements.txt
    print_success "Main dependencies installed"
    
    # Install XML parser dependencies
    if [ -f services/xml_parser/requirements.txt ]; then
        print_info "Installing XML parser dependencies..."
        sudo .venv/bin/pip install -q -r services/xml_parser/requirements.txt
        print_success "XML parser dependencies installed"
    fi
    
    # Make scripts executable
    print_info "Making scripts executable..."
    sudo chmod +x run.sh update.sh
    print_success "Scripts are now executable"
}

initialize_database() {
    print_info "Initializing database..."
    
    cd "$INSTALL_DIR"
    
    # Set database URL
    export PVAPP_DB_URL="sqlite:///./db.sqlite3"
    
    # Initialize database
    sudo -E .venv/bin/python -c "from app.database import init_db; init_db()"
    print_success "Database initialized"
}

create_env_file() {
    print_info "Creating .env configuration file..."
    
    cd "$INSTALL_DIR"
    
    # Create .env file with default values
    sudo tee .env > /dev/null <<EOF
# Database Configuration
PVAPP_DB_URL=sqlite:///./db.sqlite3

# XML Parser Microservice Configuration
XML_PARSER_URL=http://localhost:5000

# Optional: Authentication token for the XML parser service
# XML_PARSER_TOKEN=

# Optional: Timeout for XML parser requests in seconds (default: 30)
# XML_PARSER_TIMEOUT=30
EOF
    
    print_success ".env file created"
}

create_pvapp_service() {
    print_info "Creating pvapp.service systemd unit..."
    
    sudo tee /etc/systemd/system/pvapp.service > /dev/null <<EOF
[Unit]
Description=PVApp Backend Service
After=network.target

[Service]
Type=simple
User=$PVAPP_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/.venv/bin"
Environment="PVAPP_DB_URL=sqlite:///$INSTALL_DIR/db.sqlite3"
ExecStart=$INSTALL_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "pvapp.service created"
}

create_system_user() {
    print_info "Creating dedicated system user '$PVAPP_USER'..."
    
    if id "$PVAPP_USER" &>/dev/null; then
        print_warning "User $PVAPP_USER already exists"
    else
        sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$PVAPP_USER"
        print_success "User $PVAPP_USER created"
    fi
}

set_ownership() {
    print_info "Setting proper ownership and permissions..."
    
    sudo chown -R "$PVAPP_USER:$PVAPP_USER" "$INSTALL_DIR"
    print_success "Ownership set to $PVAPP_USER:$PVAPP_USER"
}

setup_systemd_services() {
    print_info "Setting up systemd services..."
    
    # Create system user
    create_system_user
    
    # Create main backend service
    create_pvapp_service
    
    # Copy XML parser service
    if [ -f "$INSTALL_DIR/pvapp-xml-parser.service" ]; then
        print_info "Installing XML parser service..."
        sudo cp "$INSTALL_DIR/pvapp-xml-parser.service" /etc/systemd/system/
        print_success "XML parser service installed"
    fi
    
    # Set ownership
    set_ownership
    
    # Reload systemd
    print_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    print_success "Systemd daemon reloaded"
    
    # Enable services
    print_info "Enabling services..."
    sudo systemctl enable pvapp
    if [ -f /etc/systemd/system/pvapp-xml-parser.service ]; then
        sudo systemctl enable pvapp-xml-parser
    fi
    print_success "Services enabled"
    
    # Start services
    print_info "Starting services..."
    sudo systemctl start pvapp
    if [ -f /etc/systemd/system/pvapp-xml-parser.service ]; then
        sudo systemctl start pvapp-xml-parser
    fi
    print_success "Services started"
}

print_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Installation directory: ${BLUE}$INSTALL_DIR${NC}"
    echo ""
    
    if [ "$SETUP_SYSTEMD" = "yes" ]; then
        echo "Services have been installed and started:"
        echo "  • pvapp (main backend) - http://localhost:8000"
        echo "  • pvapp-xml-parser (XML parser) - http://localhost:5000"
        echo ""
        echo "Service management commands:"
        echo "  sudo systemctl status pvapp"
        echo "  sudo systemctl status pvapp-xml-parser"
        echo "  sudo systemctl restart pvapp"
        echo "  sudo systemctl restart pvapp-xml-parser"
        echo ""
        echo "View logs:"
        echo "  sudo journalctl -u pvapp -f"
        echo "  sudo journalctl -u pvapp-xml-parser -f"
    else
        echo "To start the application manually:"
        echo "  cd $INSTALL_DIR"
        echo "  ./run.sh"
        echo ""
        echo "Or install systemd services:"
        echo "  cd $INSTALL_DIR"
        echo "  sudo cp pvapp-xml-parser.service /etc/systemd/system/"
        echo "  # Create pvapp.service manually or run this script again with systemd setup"
    fi
    echo ""
    echo "API documentation: http://localhost:8000/docs"
    echo ""
    echo "To update the application:"
    echo "  cd $INSTALL_DIR"
    echo "  ./update.sh"
    echo ""
}

# Main installation flow
main() {
    print_header
    
    # Check if running as root
    check_root
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Install system dependencies
    install_system_dependencies
    
    # Step 3: Install application
    install_application
    
    # Step 4: Initialize database
    initialize_database
    
    # Step 5: Create .env file
    create_env_file
    
    # Step 6: Ask about systemd services
    echo ""
    print_info "Do you want to install and start systemd services?"
    print_info "This will create a dedicated 'pvapp' user and set up automatic startup"
    read -p "Install systemd services? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SETUP_SYSTEMD="yes"
        setup_systemd_services
    else
        SETUP_SYSTEMD="no"
        print_info "Skipping systemd setup"
    fi
    
    # Print completion message
    print_completion
}

# Run main function
main "$@"
