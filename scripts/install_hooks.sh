#!/bin/bash
#
# Script to install development hooks and tools for MANTA
#

echo "=== Setting up development environment for MANTA ==="

# Check if python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 could not be found. Please install Python 3.9 or later."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_VERSION_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_VERSION_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_VERSION_MAJOR" -lt 3 ] || ([ "$PYTHON_VERSION_MAJOR" -eq 3 ] && [ "$PYTHON_VERSION_MINOR" -lt 9 ]); then
    echo "❌ Python 3.9 or later is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Install development dependencies
echo "Installing development dependencies..."
if pip install -e ".[dev]"; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
if pre-commit install; then
    echo "✅ Pre-commit hooks installed successfully"
else
    echo "❌ Failed to install pre-commit hooks"
    exit 1
fi

# Initialize initial hooks run
echo "Running initial pre-commit check..."
pre-commit run --all-files

echo ""
echo "=== MANTA development environment setup complete ==="
echo ""
echo "Next steps:"
echo "1. Run tests: pytest tests/"
echo "2. Start the application: python3 camera/main.py"
echo "3. Check documentation: docs/developer-guide.md"
echo ""