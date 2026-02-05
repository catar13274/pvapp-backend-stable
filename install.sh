#!/bin/bash

# PVApp Backend - Installation Script
echo "================================"
echo "PVApp Backend - Installation"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: "+$(python3 --version)"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo "❌ Python version must be 3.8 or higher. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version is compatible"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models
mkdir -p logs
mkdir -p data
echo "✅ Directories created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./pvapp.db

# Llama Model Configuration
LLAMA_MODEL_PATH=./models/llama-3-8b.gguf

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security (Generate a secure secret key)
SECRET_KEY=your-secret-key-here-change-this

# CORS Origins (comma separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment
ENVIRONMENT=development
EOF
    echo "✅ .env file created (please update with your settings)"
else
    echo "ℹ️  .env file already exists"
fi
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app.database import create_db_and_tables; create_db_and_tables()"

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully"
else
    echo "⚠️  Database initialization skipped or failed (will be created on first run)"
fi
echo ""
echo "================================"
echo "✅ Installation Complete!"
echo "================================"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the server: uvicorn app.main:app --reload"
echo ""
echo "Or use the provided scripts:"
echo "  ./start.sh      - Start the application"
echo "  ./update.sh     - Update dependencies"
echo "  ./uninstall.sh  - Remove installation"
echo ""
echo "Access the API at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""