# 🤖 Distributed Robot System

> **Modular robotics platform with PC-based AI processing and Raspberry Pi hardware interface**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B%2B%2F4-red.svg)](https://www.raspberrypi.org/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Hardware Requirements](#-hardware-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Module Documentation](#-module-documentation)
- [Network Setup](#-network-setup)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

This project implements a **distributed robotics system** where a powerful Ubuntu PC handles all intensive processing (AI, SLAM, face animation, voice synthesis) while a Raspberry Pi 3B+ serves as a lightweight hardware interface for motors, sensors, camera, and display.

### Why Distributed Architecture?

- **Eliminates Pi Processing Lag**: All heavy computation runs on PC
- **Real-time Performance**: Sub-100ms response times
- **Modular Design**: Easy to extend and modify components
- **Resource Efficient**: Pi 3B+ handles only I/O streaming
- **Scalable**: Can support multiple robots from one PC

### Key Capabilities

✅ **Voice-Controlled Navigation** - Natural language movement commands  
✅ **Interactive Face Display** - Dynamic eyes/mouth with real-time lip-sync  
✅ **SLAM Mapping** - RP-LIDAR A1 based simultaneous localization and mapping  
✅ **AI Conversation** - Google Gemini integration for intelligent responses  
✅ **Multi-Sensor Fusion** - Camera, LiDAR, ultrasonic obstacle detection  
✅ **Web Dashboard** - Real-time monitoring and manual control  
✅ **Emergency Safety** - Automatic motor shutoff on exit/obstacles  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       UBUNTU PC (Processing Hub)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Gemini AI   │  │  SLAM Engine │  │ Face Animator│         │
│  │   (Speech)   │  │  (Mapping)   │  │  (Lip-Sync)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Edge TTS     │  │ Vision Proc  │  │  Dashboard   │         │
│  │ (Synthesis)  │  │  (Camera)    │  │   (Flask)    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                   WebSocket (WiFi/Ethernet)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  RASPBERRY PI 3B+ (Hardware I/O)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Motor Driver │  │  RP-LIDAR A1 │  │  Camera OV   │         │
│  │  (4x DC)     │  │  (Scanning)  │  │  (Streaming) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Ultrasonic   │  │  USB Mic     │  │ 10.1" Touch  │         │
│  │  (HC-SR04)   │  │  (Audio In)  │  │   Display    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Voice Input**: Mic → Pi → PC (Speech Recognition) → Gemini AI
2. **Movement**: AI Decision → PC → Pi (Motor Control)
3. **Face Animation**: TTS Phonemes → PC (Keyframe Generation) → Pi Display
4. **Sensor Fusion**: Camera/LiDAR/Ultrasonic → Pi → PC (SLAM/Vision)
5. **Audio Output**: PC (Edge TTS) → Pi Speakers

---

## ✨ Features

### 🎙️ Voice Interaction
- **Natural Language Processing**: "Move forward for 3 seconds", "Turn left"
- **Google Gemini AI**: Context-aware conversations
- **Edge TTS**: High-quality Indian English voice synthesis
- **Real-time Response**: <200ms latency

### 👁️ Animated Face Display
- **Dynamic Eyes**: Blinking, gaze tracking
- **Phoneme-Based Lip Sync**: Mouth shapes sync with speech
- **60 FPS Canvas Rendering**: Smooth animations on 10.1" display
- **Emotional Expressions**: Configurable moods

### 🗺️ SLAM Navigation
- **RP-LIDAR A1 Integration**: 360° laser scanning
- **Real-time Mapping**: Build environment maps while moving
- **Path Planning**: Autonomous navigation to waypoints
- **Obstacle Avoidance**: Ultrasonic + LiDAR fusion

### 🎮 Control Interfaces
- **Voice Commands**: Hands-free operation
- **Web Dashboard**: Visual control panel with live feeds
- **Keyboard Control**: WASD/Arrow keys for manual driving
- **Mobile Responsive**: Control from phone/tablet

### 🛡️ Safety Systems
- **Emergency Stop**: Multiple redundant shutdown mechanisms
- **Obstacle Detection**: Auto-stop when distance < 30cm
- **Signal Handlers**: Clean shutdown on SIGINT/SIGTERM
- **Motor Lock Prevention**: Guaranteed GPIO cleanup

---

## 🔧 Hardware Requirements

### PC Server (Ubuntu 20.04/22.04)
- **CPU**: Intel i5/Ryzen 5 or better
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional (improves vision processing)
- **Network**: Ethernet/WiFi with static IP

### Raspberry Pi Client
| Component | Model | Purpose |
|-----------|-------|----------|
| **SBC** | Raspberry Pi 3B+ or 4 | Main controller |
| **Camera** | OV5647 / USB Webcam | Video streaming |
| **LiDAR** | RP-LIDAR A1 | SLAM mapping |
| **Motors** | 4x DC Motors | Differential drive |
| **Motor Driver** | L298N / BTS7960 | Motor control |
| **Ultrasonic** | HC-SR04 | Obstacle detection |
| **Microphone** | USB Microphone | Voice input |
| **Speakers** | USB/3.5mm Speakers | Audio output |
| **Display** | 10.1" Touch LCD | Face animation |
| **Power** | 12V Battery + 5V Step-down | Power supply |

### Pin Configuration (Raspberry Pi)

```python
# Motor Pins (GPIO BOARD numbering)
L1: 33  # Left Motor Forward
L2: 38  # Left Motor Backward
R1: 35  # Right Motor Forward
R2: 40  # Right Motor Backward

# Relay Pins (Optional)
Relay 1: 15
Relay 2: 16
Relay 3: 18
Relay 4: 22

# Ultrasonic Sensor
Trigger: 11
Echo: 13
```

---

## 📥 Installation

### Prerequisites

**Both Systems:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git python3-pip python3-venv -y
```

### Clone Repository

```bash
git clone https://github.com/vivan129/distributed-robot-system.git
cd distributed-robot-system
```

### PC Server Setup

```bash
cd pc_server
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install system audio dependencies
sudo apt install portaudio19-dev -y

# Optional: ROS for advanced SLAM
# sudo apt install ros-noetic-desktop-full
```

### Raspberry Pi Setup

```bash
cd pi_client
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install system dependencies
sudo apt install mpg123 -y

# Enable camera and I2C
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_i2c 0

# Add user to GPIO group
sudo usermod -a -G gpio $USER
```

### Quick Install Scripts

```bash
# PC
chmod +x scripts/setup_pc.sh
./scripts/setup_pc.sh

# Pi
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```

---

## 🚀 Quick Start

### 1. Configure Network

Edit `config/robot_config.yaml`:

```yaml
pc_ip: "192.168.1.100"    # Your PC's static IP
pc_port: 5000
pi_ip: "192.168.1.101"    # Your Pi's static IP
pi_display_port: 8080
```

### 2. Set API Keys

**On PC**, create `.env` file:

```bash
GEMINI_API_KEY="your_google_gemini_api_key_here"
```

Get your key at: https://ai.google.dev/

### 3. Start PC Server

```bash
cd pc_server
source venv/bin/activate
python main.py
```

**Expected Output:**
```
============================================================
🖥️  ROBOT PC SERVER STARTING
============================================================
✓ Gemini AI connected
✓ TTS engine initialized
✓ Face animator ready
🌐 Dashboard: http://192.168.1.100:5000
🤖 Waiting for Raspberry Pi at 192.168.1.101...
============================================================
```

### 4. Start Pi Client

```bash
cd pi_client
source venv/bin/activate
python main.py
```

**Expected Output:**
```
============================================================
🤖 RASPBERRY PI CLIENT STARTING
============================================================
✓ Motors initialized (all OFF)
✓ Camera: OpenCV (640x480)
✓ RP-LIDAR A1 connected on /dev/ttyUSB0
✓ Ultrasonic sensor ready
🖥️  Face display: http://192.168.1.101:8080
✓ Connected to PC: http://192.168.1.100:5000
============================================================
```

### 5. Open Interfaces

- **PC Dashboard**: `http://192.168.1.100:5000` (on any device)
- **Pi Face Display**: `http://192.168.1.101:8080` (on Pi's screen)

### 6. Test Voice Command

**Say**: *"Move forward for 3 seconds"*

**Expected Behavior**:
1. ✅ PC recognizes speech
2. ✅ Gemini processes command
3. ✅ Motors move forward for 3s
4. ✅ Face displays lip-synced response
5. ✅ TTS plays through Pi speakers

---

## ⚙️ Configuration

### Hardware Configuration

**`config/robot_config.yaml`** - Main configuration file

```yaml
# Motor pin mapping (GPIO BOARD)
motor_pins:
  L1: 33    # Left forward
  L2: 38    # Left backward
  R1: 35    # Right forward
  R2: 40    # Right backward

# Camera settings
camera_type: "opencv"      # or "picamera2"
camera_width: 640
camera_height: 480
camera_fps: 30

# LiDAR
lidar_port: "/dev/ttyUSB0"
lidar_baudrate: 115200

# Safety
obstacle_threshold: 30     # cm
```

### SLAM Configuration

**`config/slam_config.yaml`** - SLAM parameters

```yaml
map_resolution: 0.05        # meters per pixel
map_size: [2000, 2000]      # pixels
lidar_range_min: 0.15       # meters
lidar_range_max: 12.0       # meters
update_frequency: 10        # Hz
```

### Network Troubleshooting

**Find your IPs:**
```bash
# On PC
hostname -I

# On Pi
hostname -I
```

**Test connectivity:**
```bash
# From Pi, ping PC
ping 192.168.1.100

# From PC, ping Pi
ping 192.168.1.101
```

**Set static IP (Pi):**
```bash
sudo nano /etc/dhcpcd.conf

# Add:
interface wlan0
static ip_address=192.168.1.101/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

---

## 📚 Module Documentation

### PC Server Modules

#### `modules/voice_input.py`
- **Purpose**: Speech-to-text conversion
- **Methods**: `recognize(audio_data)` → Returns text string
- **Backend**: Google Speech Recognition / Whisper

#### `modules/ai_brain.py`
- **Purpose**: Natural language processing and decision making
- **Methods**: `process(text)` → Returns (response, movement_command)
- **Backend**: Google Gemini 2.0 Flash

#### `modules/tts_engine.py`
- **Purpose**: Text-to-speech with phoneme timing
- **Methods**: `synthesize(text)` → Returns (audio_path, phoneme_timings)
- **Backend**: Edge TTS (Microsoft)

#### `modules/face_animator.py`
- **Purpose**: Generate lip-sync animation keyframes
- **Methods**: `generate_lipsync(phonemes)` → Returns animation data
- **Algorithm**: Phoneme-to-viseme mapping with interpolation

#### `modules/slam_processor.py`
- **Purpose**: SLAM mapping and localization
- **Methods**: `add_scan(ranges, angles)`, `get_current_map()`
- **Algorithm**: Grid-based occupancy mapping

### Pi Client Modules

#### `hardware/motor_controller.py`
- **Purpose**: DC motor control with safety
- **Methods**: `move(direction)`, `stop()`, `cleanup()`
- **Safety**: Multiple shutdown handlers, emergency stop

#### `hardware/camera_streamer.py`
- **Purpose**: Stream camera frames to PC
- **Methods**: `stream()` → Async generator of frames
- **Formats**: OpenCV / Picamera2

#### `hardware/lidar_streamer.py`
- **Purpose**: Stream RP-LIDAR scans to PC
- **Methods**: `stream()` → Async generator of scans
- **Driver**: rplidar-roboticia

#### `display/face_display.py`
- **Purpose**: Render face animations from PC
- **Methods**: Receives keyframes via WebSocket
- **Renderer**: HTML5 Canvas (60 FPS)

---

## 🌐 Network Setup

### Architecture

```
[Router 192.168.1.1]
      |
      ├── [PC Server: 192.168.1.100:5000]
      |       ├── Flask web server
      |       ├── SocketIO server (/pc, /pi namespaces)
      |       └── Processing modules
      |
      └── [Pi Client: 192.168.1.101]
              ├── SocketIO client → PC:5000/pi
              └── Local display server :8080
```

### WebSocket Events

#### PC → Pi
| Event | Data | Purpose |
|-------|------|----------|
| `movement_command` | `{direction, duration}` | Control motors |
| `stop_command` | `{}` | Emergency stop |
| `face_animation` | `{keyframes, duration}` | Update face display |
| `play_audio` | `{audio_data}` | Play TTS on speakers |

#### Pi → PC
| Event | Data | Purpose |
|-------|------|----------|
| `camera_frame` | `{frame, timestamp}` | Video stream |
| `lidar_scan` | `{ranges, angles}` | SLAM data |
| `ultrasonic_data` | `{distance}` | Obstacle distance |
| `mic_audio` | `{audio}` | Voice input |

---

## 🐛 Troubleshooting

### Common Issues

#### Motors Don't Stop

**Symptoms**: Motors keep running after program exit

**Solutions**:
1. Check GPIO cleanup in `motor_controller.py`
2. Manually reset: `python -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BOARD); GPIO.setup([33,38,35,40], GPIO.OUT); GPIO.output([33,38,35,40], GPIO.LOW); GPIO.cleanup()"`
3. Hardware reset: Disconnect motor power

#### Camera Not Detected

**Symptoms**: `Camera failed` error

**Solutions**:
```bash
# Check camera
vcgencmd get_camera

# Enable camera
sudo raspi-config nonint do_camera 0
sudo reboot

# Test with OpenCV
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

#### LiDAR Connection Failed

**Symptoms**: `LiDAR connection failed: /dev/ttyUSB0`

**Solutions**:
```bash
# Find device
ls /dev/ttyUSB*

# Add user to dialout group
sudo usermod -a -G dialout $USER
sudo reboot

# Test connection
python3 -c "from rplidar import RPLidar; lidar = RPLidar('/dev/ttyUSB0'); print(lidar.get_info())"
```

#### Pi Can't Connect to PC

**Symptoms**: `PC connection failed`

**Solutions**:
1. Check PC server is running
2. Verify IPs in `robot_config.yaml`
3. Test connectivity: `ping <PC_IP>`
4. Check firewall: `sudo ufw allow 5000/tcp`
5. Verify same network/subnet

#### Face Animation Laggy

**Symptoms**: Face stutters or freezes

**Solutions**:
1. Reduce keyframe count in `face_animator.py`
2. Lower display resolution in config
3. Use hardware acceleration: Add `dtoverlay=vc4-kms-v3d` to `/boot/config.txt`
4. Close unnecessary Pi processes

#### Audio Issues

**Symptoms**: No sound from speakers

**Solutions**:
```bash
# List audio devices
aplay -l

# Test playback
speaker-test -t wav

# Set default device
sudo nano /etc/asound.conf
# Add:
pcm.!default {
    type hw
    card 1
}

# Test TTS
mpg123 test.mp3
```

---

## 🎯 Usage Examples

### Voice Commands

```
"Move forward for 5 seconds"
"Turn left"
"Go backward for 2 seconds"
"Stop"
"Tell me a joke"
"What's the weather like?"
```

### Python API

**Send custom command from PC:**
```python
from modules.robot_controller import RobotController

robot = RobotController(config, socketio)
await robot.send_movement({'direction': 'forward', 'duration': 3})
await robot.send_stop()
```

**Create custom face expression:**
```python
from modules.face_animator import FaceAnimator

face = FaceAnimator(config)
animation = face.generate_expression('happy')  # surprised, sad, angry
socketio.emit('face_animation', animation, room='pi_display')
```

**Get SLAM map:**
```python
from modules.slam_processor import SLAMProcessor

slam = SLAMProcessor(config)
map_data = slam.get_current_map()
slam.save_map('room_map.pgm')
```

---

## 🔮 Roadmap

### Phase 1: Core Functionality ✅
- [x] Distributed architecture
- [x] Motor control with safety
- [x] Voice interaction
- [x] Face animation with lip-sync
- [x] Basic sensor integration

### Phase 2: Advanced Features 🚧
- [ ] Full SLAM implementation
- [ ] Autonomous navigation
- [ ] Object detection (YOLO)
- [ ] Multi-robot coordination
- [ ] Mobile app interface

### Phase 3: AI Enhancement 📋
- [ ] Visual question answering
- [ ] Person recognition
- [ ] Gesture control
- [ ] Emotion recognition
- [ ] Long-term memory

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new modules
- Update documentation for API changes
- Test on actual hardware before PR

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** - Natural language processing
- **Microsoft Edge TTS** - High-quality voice synthesis
- **RP-LIDAR** - Affordable laser scanning
- **Raspberry Pi Foundation** - Accessible computing platform
- **Flask-SocketIO** - Real-time communication

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/vivan129/distributed-robot-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vivan129/distributed-robot-system/discussions)
- **Documentation**: [Wiki](https://github.com/vivan129/distributed-robot-system/wiki)

---

## 🌟 Star History

If this project helped you, please ⭐ star the repository!

---

**Built with ❤️ for the maker community**

*Last Updated: January 2026*