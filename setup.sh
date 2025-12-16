#!/bin/bash
# Setup script for RiceDB Python client

echo "🍚 RiceDB Python Client Setup"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the ricedb-python directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "1️⃣  Creating virtual environment with uv..."
    uv venv
    echo "   ✓ Created .venv"
else
    echo "1️⃣  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "2️⃣  Activating virtual environment..."
source .venv/bin/activate
echo "   ✓ Activated .venv"

# Install the package in development mode
echo ""
echo "3️⃣  Installing RiceDB client with uv..."
uv pip install -e ".[dev,grpc]"

# Check installation
echo ""
echo "4️⃣  Verifying installation..."
python -c "import ricedb; print(f'   ✓ RiceDB version {ricedb.__version__} installed')"

# Show example usage
echo ""
echo "5️⃣  Example usage:"
echo "   python examples/basic_usage.py"
echo ""
echo "   Or in Python:"
echo "   >>> from ricedb import RiceDBClient"
echo "   >>> client = RiceDBClient()"
echo "   >>> client.connect()"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start a RiceDB server (HTTP or gRPC)"
echo "2. Run the examples: python examples/basic_usage.py"
echo "3. Check the documentation in README.md"
