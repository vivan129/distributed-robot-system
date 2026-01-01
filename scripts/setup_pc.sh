#!/bin/bash
# PC Server Setup Script
# Run this on your Ubuntu PC

set -e  # Exit on error

echo "============================================================"
echo "💻  ROBOT PC SERVER SETUP"
echo "============================================================"
echo ""

# Check if running on Ubuntu/Debian
if ! [ -f /etc/debian_version ]; then
    echo "⚠️  This script is designed for Ubuntu/Debian systems"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    portaudio19-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev

echo ""
echo "Step 3: Setting up Python virtual environment..."
cd "$(dirname "$0")/../pc_server" || exit

if [ -d "venv" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo ""
echo "Step 4: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Step 5: Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 6: Setting up environment variables..."
if [ ! -f "../.env" ]; then
    cp ../.env.example ../.env
    echo "✓ Created .env file from template"
    echo "⚠️  IMPORTANT: Edit .env file and add your GEMINI_API_KEY"
    echo "   Get your key at: https://ai.google.dev/"
else
    echo ".env file already exists"
fi

echo ""
echo "Step 7: Setting up configuration..."
if [ ! -f "../config/robot_config.yaml" ]; then
    echo "⚠️  Configuration file not found!"
    echo "   Make sure config/robot_config.yaml exists"
else
    echo "✓ Configuration file found"
fi

echo ""
echo "Step 8: Testing installation..."
if python -c "import flask, socketio, google.generativeai; print('✓ All modules imported successfully')"; then
    echo "✓ Python dependencies verified"
else
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "✓ PC SERVER SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Edit config/robot_config.yaml with your network settings"
echo "3. Start server: cd pc_server && source venv/bin/activate && python main.py"
echo ""
echo "Dashboard will be available at: http://localhost:5000"
echo "============================================================"
