#!/bin/bash

# Start Jupyter Notebook Server for MCP Integration
# This script starts Jupyter with the correct parameters

echo "🚀 Starting Jupyter Notebook Server for MCP Integration..."
echo "=================================================="

# Check if jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo "❌ Jupyter is not installed. Please install it first:"
    echo "   pip install jupyter"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NOTEBOOKS_DIR="$PROJECT_ROOT/notebooks"

# Create notebooks directory if it doesn't exist
mkdir -p "$NOTEBOOKS_DIR"

# Change to notebooks directory
cd "$NOTEBOOKS_DIR"

echo "📁 Working directory: $NOTEBOOKS_DIR"
echo "📓 Notebooks will be created in this directory"

# Start Jupyter with proper configuration for newer versions
echo "📡 Starting Jupyter on http://localhost:8888"
echo "🔑 No token required for local development"
echo ""
echo "⚠️  For production use, consider adding a token:"
echo "   jupyter notebook --port=8888 --no-browser --allow-root --NotebookApp.token='your-secure-token'"
echo ""

# For newer Jupyter versions (6.0+) - the correct way
echo "🔧 Using modern Jupyter configuration..."
jupyter notebook \
    --port=8888 \
    --no-browser \
    --allow-root \
    --ip=127.0.0.1 \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --NotebookApp.disable_check_xsrf=True \
    --NotebookApp.allow_origin='*' \
    --NotebookApp.allow_credentials=True

# If the above fails, try with ServerApp (Jupyter 7.0+)
if [ $? -ne 0 ]; then
    echo ""
    echo "🔄 Trying with Jupyter 7.0+ ServerApp configuration..."
    jupyter notebook \
        --port=8888 \
        --no-browser \
        --allow-root \
        --ip=127.0.0.1 \
        --ServerApp.token='' \
        --ServerApp.password='' \
        --ServerApp.disable_check_xsrf=True \
        --ServerApp.allow_origin='*' \
        --ServerApp.allow_credentials=True
fi 