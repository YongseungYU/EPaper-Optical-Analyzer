#!/bin/bash
set -e

echo "=========================================="
echo " E-Paper Optical Analyzer - Build Script"
echo "=========================================="

# Check Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found. Please install Python 3.8+."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Using: $PYTHON_VERSION"

# Change to script directory
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"

# Create or activate virtual environment
if [ -d "venv" ]; then
    echo "Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements_desktop.txt

# Run PyInstaller
echo ""
echo "Building executable with PyInstaller..."
pyinstaller epaper_analyzer.spec --clean

echo ""
echo "=========================================="
echo " Build Complete!"
echo "=========================================="
echo " Output: dist/EPaper_Optical_Analyzer/"
echo "=========================================="
