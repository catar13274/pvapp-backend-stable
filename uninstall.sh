#!/bin/bash

# PVApp Backend - Uninstallation Script
echo "================================"
echo "PVApp Backend - Uninstallation"
echo "================================"
echo ""
echo "⚠️  WARNING: This will remove all installed files and data!"
echo ""

# Ask for confirmation
read -p "Are you sure you want to uninstall? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Uninstallation cancelled"
    exit 0
fi

echo ""
echo "Starting uninstallation..."
echo ""

# Stop any running instances
echo "🛑 Stopping any running instances..."
pkill -f "uvicorn app.main:app" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Stopped running application"
else
    echo "ℹ️  No running instances found"
fi
echo ""

# Remove virtual environment
if [ -d "venv" ]; then
    echo "🗑️  Removing virtual environment..."
    rm -rf venv
    echo "✅ Virtual environment removed"
else
    echo "ℹ️  Virtual environment not found"
fi
echo ""

# Ask about database
read -p "Do you want to remove the database? (yes/no): " remove_db

if [ "$remove_db" = "yes" ]; then
    if [ -f "pvapp.db" ]; then
        echo "🗑️  Removing database..."
        rm -f pvapp.db
        echo "✅ Database removed"
    else
        echo "ℹ️  Database not found"
    fi
fi
echo ""

# Ask about .env file
read -p "Do you want to remove the .env file? (yes/no): " remove_env

if [ "$remove_env" = "yes" ]; then
    if [ -f ".env" ]; then
        echo "🗑️  Removing .env file..."
        rm -f .env
        echo "✅ .env file removed"
    else
        echo "ℹ️  .env file not found"
    fi
fi
echo ""

# Ask about logs and data directories
read -p "Do you want to remove logs and data directories? (yes/no): " remove_data

if [ "$remove_data" = "yes" ]; then
    echo "🗑️  Removing logs and data..."
    rm -rf logs
    rm -rf data
    echo "✅ Logs and data removed"
else
    echo "ℹ️  Keeping logs and data directories"
fi
echo ""

# Remove __pycache__ directories
echo "🧹 Cleaning up Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✅ Python cache cleaned"
echo ""
echo "================================"
echo "✅ Uninstallation Complete!"
echo "================================"
echo ""
echo "Kept files:"
echo "  - Source code (app/)"
echo "  - Requirements (requirements.txt)"
echo "  - Scripts (install.sh, update.sh)"
if [ "$remove_db" != "yes" ]; then
    echo "  - Database (pvapp.db)"
fi
if [ "$remove_env" != "yes" ]; then
    echo "  - Configuration (.env)"
fi
if [ "$remove_data" != "yes" ]; then
    echo "  - Logs and data directories"
fi
echo ""
echo "To reinstall, run: ./install.sh"
echo ""