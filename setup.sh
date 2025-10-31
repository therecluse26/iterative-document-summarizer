#!/usr/bin/env bash
# Quick setup script for AI Sliding Context Summarizer

set -e

echo "=================================="
echo "AI Sliding Context Summarizer"
echo "Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Check for BAML CLI
echo "Checking for BAML CLI..."
if ! command -v baml-cli &> /dev/null; then
    echo "Warning: baml-cli not found. Install it with: npm install -g @boundaryml/baml"
    echo "Continuing anyway..."
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (required)"
    echo "   - OPENAI_API_KEY (optional)"
    echo ""
fi

# Generate BAML client
if command -v baml-cli &> /dev/null; then
    echo "Generating BAML client code..."
    baml-cli generate --from ./baml --output ./baml_client
    echo "✓ BAML client generated successfully"
else
    echo "⚠️  Skipping BAML client generation (baml-cli not found)"
    echo "   Install baml-cli and run: baml-cli generate --from ./baml --output ./baml_client"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. (If baml-cli wasn't found) Install it and run:"
echo "   npm install -g @boundaryml/baml"
echo "   baml-cli generate --from ./baml --output ./baml_client"
echo "3. Run the example:"
echo "   source venv/bin/activate"
echo "   python src/orchestrator.py example_input.txt"
echo ""
