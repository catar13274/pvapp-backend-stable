#!/bin/bash
# Quick fix script for database migration
# Adds missing columns for invoice upload feature

echo "============================================"
echo "PV Management App - Database Fix"
echo "============================================"
echo ""

# Detect script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "scripts/migrate_db.py" ]; then
    echo "Error: migrate_db.py not found!"
    echo "Please run this script from the /opt/pvapp directory"
    exit 1
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Run migration
echo "Running database migrations..."
echo ""
python scripts/migrate_db.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database fixed successfully!"
    echo ""
    echo "Now restart the application:"
    echo "  sudo systemctl restart pvapp"
    echo ""
    echo "Or if running manually:"
    echo "  # Stop the current process (Ctrl+C)"
    echo "  # Then start again:"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
else
    echo ""
    echo "✗ Migration failed. Check the error messages above."
    echo ""
    exit 1
fi
