#!/bin/bash

# Mapy Image Manager - Startup Script

set -e

echo "========================================="
echo "Mapy Image Manager"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python -c "from database import Database; db = Database(); print(f'Database initialized: {db.db_path}')"

# Create necessary directories
mkdir -p data uploads exports

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file not found!"
    echo "Copy .env.example to .env and add your SerpAPI key:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
fi

# Display startup info
echo ""
echo "========================================="
echo "Starting Mapy Image Manager"
echo "========================================="
echo ""
echo "Server will be available at:"
echo "  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
uvicorn app:app --reload --host 0.0.0.0 --port 8000
