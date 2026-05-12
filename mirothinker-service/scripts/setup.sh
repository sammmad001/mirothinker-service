#!/usr/bin/env bash
# MiroThinker Service - Setup Script
# Sets up development environment and installs dependencies

set -e

echo "========================================"
echo "MiroThinker Service - Environment Setup"
echo "========================================"

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python: $PYTHON_VERSION"

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev,monitoring]"

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please edit .env and add your DASHSCOPE_API_KEY"
else
    echo ".env file already exists, skipping"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/{traces,logs,cache}

# Run tests
echo "Running tests..."
pytest backend/tests -v --tb=short

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your DASHSCOPE_API_KEY"
echo "2. Run 'make run' to start development server"
echo "3. Visit http://localhost:8000"
echo ""
