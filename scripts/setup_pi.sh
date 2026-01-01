#!/bin/bash
# Raspberry Pi Client Setup Script
# Run this on your Raspberry Pi

set -e  # Exit on error

echo "============================================================"
echo "🤖  RASPBERRY PI CLIENT SETUP"
echo "============================================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  This doesn't appear to be a Raspberry Pi"
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
    python3-rpi.gpio \
    git \
    mpg123 \
    libatlas-base-dev \
    libopenblas-dev \
    python3-opencv

echo ""
echo "Step 3: Enabling camera and I2C..."
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_i2c 0

echo ""
echo "Step 4: Adding user to GPIO and dialout groups..."
sudo usermod -a -G gpio $USER
sudo usermod -a -G dialout $USER
echo "⚠️  Note: You may need to log out and back in for group changes to take effect"

echo ""
echo "Step 5: Setting up Python virtual environment..."
cd "$(dirname "$0")/../pi_client" || exit

if [ -d "venv" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

echo ""
echo "Step 6: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Step 7: Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 8: Setting up configuration..."
if [ ! -f "../config/robot_config.yaml" ]; then
    echo "⚠️  Configuration file not found!"
    echo "   Make sure config/robot_config.yaml exists"
else
    echo "✓ Configuration file found"
    echo "⚠️  Update PC and Pi IP addresses in config/robot_config.yaml"
fi

echo ""
echo "Step 9: Setting USB permissions for LiDAR..."
if [ -e "/dev/ttyUSB0" ]; then
    sudo chmod 666 /dev/ttyUSB0
    echo "✓ USB0 permissions set"
else
    echo "⚠️  /dev/ttyUSB0 not found (LiDAR not connected)"
fi

echo ""
echo "Step 10: Testing installation..."
if python -c "import RPi.GPIO as GPIO, cv2, flask; print('✓ All modules imported successfully')"; then
    echo "✓ Python dependencies verified"
else
    echo "❌ Import test failed"
    exit 1
fi

echo ""
echo "Step 11: Testing GPIO..."
if python -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BOARD); GPIO.cleanup(); print('✓ GPIO test passed')"; then
    echo "✓ GPIO accessible"
else
    echo "❌ GPIO test failed - check permissions"
fi

echo ""
echo "============================================================"
echo "✓ RASPBERRY PI CLIENT SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Update config/robot_config.yaml with correct IP addresses"
echo "2. Connect hardware (motors, camera, LiDAR, sensors)"
echo "3. Start PC server first"
echo "4. Start Pi client: cd pi_client && source venv/bin/activate && python main.py"
echo ""
echo "Face display will be available at: http://$(hostname -I | awk '{print $1}'):8080"
echo "============================================================"
echo ""
echo "⚠️  IMPORTANT: Log out and back in for group permissions to take effect!"
echo "============================================================"
