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

### 3. Setup PC Server

```bash
cd pc_server
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
nano .env  # Add your GEMINI_API_KEY
```

### 4. Setup Raspberry Pi Client

```bash
cd pi_client
pip install -r requirements.txt

# Configure Pi settings
nano ../config/robot_config.yaml
```

### 5. Run the System

**On PC:**
```bash
cd pc_server
python3 app.py
```

**On Raspberry Pi:**
```bash
cd pi_client
python3 client.py
```

## 📁 Project Structure

```
distributed-robot-system/
├── config/
│   └── robot_config.yaml      # Configuration file
├── pc_server/                  # Server-side code (PC)
│   ├── app.py                 # Flask server
│   ├── modules/
│   │   ├── ai_brain.py       # NEW google-genai SDK
│   │   ├── voice_handler.py  # Speech recognition
│   │   └── vision_processor.py
│   └── requirements.txt
├── pi_client/                  # Client-side code (Raspberry Pi)
│   ├── client.py
│   ├── modules/
│   │   ├── motor_controller.py
│   │   ├── camera_module.py
│   │   └── lidar_module.py
│   └── requirements.txt
├── tests/                      # Test suites
├── docs/                       # Documentation
│   └── GEMINI_SDK_MIGRATION.md
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
  pins:
    left_forward: 17
    left_backward: 27
    right_forward: 22
    right_backward: 23
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Gemini SDK Migration Guide](docs/GEMINI_SDK_MIGRATION.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🆕 Google Gemini SDK Update

**IMPORTANT:** This project now uses the NEW `google-genai` SDK.

- ❌ **OLD (Deprecated):** `google-generativeai` - No longer works
- ✅ **NEW (Required):** `google-genai>=0.2.0`

**Requirements:**
- Python 3.9+
- pip 21.0+

See [GEMINI_SDK_MIGRATION.md](docs/GEMINI_SDK_MIGRATION.md) for full details.

## 🐛 Troubleshooting

### "Could not find a version for google-genai"

```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Try installing directly
pip install google-genai --upgrade

# If still fails, check Python version
python3 --version  # Must be 3.9+
```

### Old SDK Installed

```bash
# Remove deprecated package
pip uninstall google-generativeai

# Install new SDK
pip install google-genai
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Google Gemini API](https://ai.google.dev/)
- [New SDK Documentation](https://googleapis.github.io/python-genai/)
- [GitHub Issues](https://github.com/vivan129/distributed-robot-system/issues)

## ⭐ Support

If this project helps you, please give it a star! ⭐