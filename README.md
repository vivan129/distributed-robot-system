# Distributed Robot System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A distributed architecture for controlling robots remotely - perfect for Raspberry Pi robots controlled by a PC server.

## ⚠️ Requirements

- **Python 3.9 or higher** (Required for google-genai SDK)
- **pip 21.0+** (Run: `python3 -m pip install --upgrade pip`)
- Raspberry Pi (3/4/5) with camera and motors
- PC/Laptop for server
- Network connectivity between devices

## 🚀 Quick Start

### 1. Check Python Version

```bash
python3 --version  # Must be 3.9 or higher
```

**If you have Python 3.8 or lower:**
```bash
# Ubuntu/Debian - Install Python 3.9+
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev

# Use Python 3.9 for this project
python3.9 -m venv venv
source venv/bin/activate
```

### 2. Clone Repository

```bash
git clone https://github.com/vivan129/distributed-robot-system.git
cd distributed-robot-system
```

### 3. Configure Static IPs (RECOMMENDED)

**Why Static IPs?** When you move your PC and robot to different locations, DHCP-assigned IPs can change, breaking the connection. Static IPs ensure consistent communication.

**Quick Setup:**
```bash
# Run the automated setup script
chmod +x scripts/setup_static_ip.sh

# On PC
sudo ./scripts/setup_static_ip.sh pc

# On Raspberry Pi
sudo ./scripts/setup_static_ip.sh pi
```

The script will guide you through setting up:
- Static IP addresses
- Router/gateway configuration
- DNS settings
- Automatic fallback to DHCP if network changes

**Recommended IP Configuration:**
- PC Server: `192.168.1.100`
- Raspberry Pi: `192.168.1.101`
- Router/Gateway: `192.168.1.1` (check your router settings)

### 4. Setup PC Server

```bash
cd pc_server

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# Install Python packages
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
nano .env  # Add your GEMINI_API_KEY and other settings
```

### 5. Update Network Configuration

**Edit `config/robot_config.yaml` with your static IPs:**

```yaml
network:
  pc_ip: "192.168.1.100"      # Your PC's static IP
  pc_port: 5000
  pi_ip: "192.168.1.101"      # Your Pi's static IP
  connection_timeout: 10
  retry_attempts: 3
```

**To find current IP addresses:**
```bash
# On Linux/Raspberry Pi
ip addr show | grep "inet "
# or
ifconfig | grep "inet "

# On Windows
ipconfig

# On macOS
ifconfig | grep "inet "
```

### 6. Setup Raspberry Pi Client

```bash
cd pi_client

# Install system dependencies
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# Install Python packages
pip install -r requirements.txt

# Verify GPIO permissions
sudo usermod -a -G gpio $USER
```

### 7. Run the System

**On PC:**
```bash
cd pc_server
python3 main.py  # ✅ Correct: main.py not app.py
```

**On Raspberry Pi:**
```bash
cd pi_client
python3 main.py  # ✅ Correct: main.py
```

**Access Dashboard:**
Open browser to `http://192.168.1.100:5000` (or your PC's static IP)

## 📁 Project Structure

```
distributed-robot-system/
├── config/
│   └── robot_config.yaml      # Configuration file
├── pc_server/                  # Server-side code (PC)
│   ├── main.py                # ✅ Flask server (main entry point)
│   ├── modules/
│   │   ├── ai_brain.py       # NEW google-genai SDK
│   │   ├── voice_input.py    # Speech recognition
│   │   ├── tts_engine.py     # Text-to-speech
│   │   ├── face_animator.py  # Face animation
│   │   ├── vision_processor.py
│   │   ├── slam_processor.py
│   │   └── robot_controller.py
│   ├── templates/
│   │   └── dashboard.html
│   └── requirements.txt
├── pi_client/                  # Client-side code (Raspberry Pi)
│   ├── main.py                # ✅ Pi client (main entry point)
│   ├── hardware/
│   │   ├── motor_controller.py
│   │   ├── camera_module.py
│   │   └── lidar_module.py
│   ├── display/
│   │   └── face_display.py
│   └── requirements.txt
├── scripts/                    # Setup and utility scripts
│   ├── setup_static_ip.sh    # ✨ NEW: Configure static IPs
│   ├── setup_pc.sh
│   ├── setup_pi.sh
│   └── verify_setup.py
├── tests/                      # Test suites
├── docs/                       # Documentation
│   └── GEMINI_SDK_MIGRATION.md
├── logs/                       # Log files (auto-created)
├── .env.example               # Environment template
└── README.md
```

## 🔧 Configuration

Edit `config/robot_config.yaml` for your setup:

```yaml
ai:
  model: "gemini-2.0-flash-exp"
  temperature: 0.7
  max_tokens: 1024

motor:
  pin_mode: "BOARD"  # GPIO BOARD numbering
  pins:
    L1: 33  # Left motor forward
    L2: 38  # Left motor backward
    R1: 35  # Right motor forward
    R2: 40  # Right motor backward

network:
  pc_ip: "192.168.1.100"  # Static IP recommended
  pc_port: 5000
  pi_ip: "192.168.1.101"  # Static IP recommended
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Static IP Setup Guide](docs/STATIC_IP_GUIDE.md)
- [Gemini SDK Migration Guide](docs/GEMINI_SDK_MIGRATION.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Network Setup Guide](docs/NETWORK_SETUP.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 🆕 Google Gemini SDK Update

**IMPORTANT:** This project now uses the NEW `google-genai` SDK.

- ❌ **OLD (Deprecated):** `google-generativeai` - No longer works
- ✅ **NEW (Required):** `google-genai>=0.2.0`

**Requirements:**
- Python 3.9+
- pip 21.0+

See [GEMINI_SDK_MIGRATION.md](docs/GEMINI_SDK_MIGRATION.md) for full details.

## 🐛 Troubleshooting

### Connection Issues After Moving Devices

**Problem:** Robot loses connection when moved to different location.

**Solution:** Use static IP addresses (see setup guide above).

```bash
# Verify connectivity
ping 192.168.1.101  # From PC to Pi
ping 192.168.1.100  # From Pi to PC

# Check current IP
ip addr show

# Re-run static IP setup if needed
sudo ./scripts/setup_static_ip.sh
```

### "Could not find a version for google-genai"

```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Try installing directly
pip install google-genai --upgrade

# If still fails, check Python version
python3 --version  # Must be 3.9+
```

### PyAudio Installation Fails

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.14-cp39-cp39-win_amd64.whl
```

### "RPi.GPIO not found" on PC

This is normal - RPi.GPIO only works on Raspberry Pi. The PC server doesn't need it.

### Camera not detected

```bash
# Check camera
ls /dev/video*

# Test with OpenCV
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Connection refused between PC and Pi

1. **Set up static IPs** (recommended)
2. Verify both devices on same network
3. Check firewall settings:
   ```bash
   # Ubuntu/Debian - Allow port 5000
   sudo ufw allow 5000/tcp
   ```
4. Verify IPs in `robot_config.yaml`
5. Test connection: `ping YOUR_PI_IP`

### Static IP Not Working

```bash
# Check network interface name
ip link show

# Verify NetworkManager or dhcpcd configuration
sudo systemctl status NetworkManager
sudo systemctl status dhcpcd

# Restart networking
sudo systemctl restart NetworkManager
# or for Raspberry Pi OS
sudo systemctl restart dhcpcd
```

### Old SDK Installed

```bash
# Remove deprecated package
pip uninstall google-generativeai

# Install new SDK
pip install google-genai
```

## 🔒 Security Notes

**IMPORTANT:** Before deployment:

1. **Change Flask Secret Key** - Set `FLASK_SECRET_KEY` in `.env`
2. **Restrict CORS** - Update `CORS_ALLOWED_ORIGINS` in `.env`
3. **Secure API Keys** - Never commit `.env` to git
4. **Use HTTPS** - For production deployments
5. **Firewall Rules** - Only open necessary ports:
   ```bash
   sudo ufw allow from 192.168.1.101 to any port 5000  # Allow only Pi
   ```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Google Gemini API](https://ai.google.dev/)
- [New SDK Documentation](https://googleapis.github.io/python-genai/)
- [GitHub Issues](https://github.com/vivan129/distributed-robot-system/issues)
- [Raspberry Pi GPIO Guide](https://pinout.xyz/)
- [NetworkManager Documentation](https://networkmanager.dev/)

## ⭐ Support

If this project helps you, please give it a star! ⭐

---

**Made with ❤️ for robotics enthusiasts**