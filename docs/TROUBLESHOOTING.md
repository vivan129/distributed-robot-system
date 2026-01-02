# Troubleshooting Guide

Common issues and solutions for the Distributed Robot System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Issues](#connection-issues)
- [Hardware Issues](#hardware-issues)
- [Software Issues](#software-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### "Could not find a version for google-genai"

**Cause:** Python version too old or pip not upgraded.

**Solution:**
```bash
# Check Python version (must be 3.9+)
python3 --version

# Upgrade pip
python3 -m pip install --upgrade pip

# Install package
pip install google-genai --upgrade
```

### PyAudio Installation Fails

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Windows:**
1. Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Install: `pip install PyAudio-0.2.14-cp39-cp39-win_amd64.whl`

### "RPi.GPIO not found" on PC

**This is normal!** RPi.GPIO only works on Raspberry Pi.

**For development on PC:**
```bash
# Add to .env
SKIP_HARDWARE_INIT=True
```

### OpenCV Installation Issues

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-opencv
pip install opencv-python
```

**Memory issues during install:**
```bash
# Use headless version (smaller)
pip install opencv-python-headless
```

## Connection Issues

### Pi Cannot Connect to PC Server

**Check 1: Same Network**
```bash
# On PC
ipconfig   # Windows
ifconfig   # Linux/Mac

# On Pi
ifconfig

# Both should have IPs in same subnet (e.g., 192.168.1.x)
```

**Check 2: Firewall**
```bash
# Linux - Allow port 5000
sudo ufw allow 5000

# Windows - Add firewall rule in Windows Defender
```

**Check 3: Test Connection**
```bash
# From Pi to PC
ping YOUR_PC_IP

# Test port
telnet YOUR_PC_IP 5000
# or
nc -zv YOUR_PC_IP 5000
```

**Check 4: Config File**
Verify `config/robot_config.yaml`:
```yaml
network:
  pc_ip: "192.168.1.XXX"  # Your actual PC IP
  pc_port: 5000
  pi_ip: "192.168.1.YYY"  # Your actual Pi IP
```

### "Connection Refused" Error

**Cause:** PC server not running or wrong IP/port.

**Solution:**
1. Start PC server first: `python3 main.py`
2. Verify server is listening: Check console output
3. Check IP matches in config
4. Verify port not in use: `netstat -an | grep 5000`

### Dashboard Won't Load

**Check 1: Server Running**
```bash
ps aux | grep main.py
```

**Check 2: Correct URL**
```
http://YOUR_PC_IP:5000   # Not localhost if accessing remotely
```

**Check 3: Browser Console**
Open browser DevTools (F12) and check for errors.

## Hardware Issues

### Motors Not Responding

**Check 1: GPIO Permissions**
```bash
sudo usermod -a -G gpio $USER
# Logout and login again
```

**Check 2: Pin Configuration**
Verify `config/robot_config.yaml`:
```yaml
motors:
  pin_mode: "BOARD"  # or "BCM"
  pins:
    L1: 33  # Check these match your wiring
    L2: 38
    R1: 35
    R2: 40
```

**Check 3: Power Supply**
- Motors need external power (not from Pi)
- Check motor driver connections
- Verify common ground between Pi and motor driver

**Check 4: Test Motors Directly**
```python
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(33, GPIO.OUT)
GPIO.output(33, GPIO.HIGH)
# Motor should activate
```

### Camera Not Detected

**Check 1: Camera Connected**
```bash
# Check for camera device
ls /dev/video*

# Should show /dev/video0 or similar
```

**Check 2: Camera Enabled**
```bash
# For Pi Camera (CSI)
sudo raspi-config
# Interface Options -> Camera -> Enable

# Reboot
sudo reboot
```

**Check 3: Test Camera**
```bash
# USB Camera
v4l2-ctl --list-devices

# Pi Camera
libcamera-hello
```

**Check 4: OpenCV Test**
```python
import cv2
cap = cv2.VideoCapture(0)
print(cap.isOpened())  # Should be True
```

### LiDAR Not Working

**Check 1: USB Connection**
```bash
ls /dev/ttyUSB*
# Should show /dev/ttyUSB0
```

**Check 2: Permissions**
```bash
sudo usermod -a -G dialout $USER
# Logout and login
```

**Check 3: Port Configuration**
Verify in `config/robot_config.yaml`:
```yaml
lidar:
  enabled: true
  port: "/dev/ttyUSB0"
  baudrate: 115200
```

### Ultrasonic Sensor Issues

**Check 1: Wiring**
- VCC to 5V
- GND to GND
- Trig to GPIO (check config)
- Echo to GPIO via voltage divider (3.3V max!)

**Check 2: Test Sensor**
```python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
TRIG = 11
ECHO = 13

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Trigger pulse
GPIO.output(TRIG, GPIO.HIGH)
time.sleep(0.00001)
GPIO.output(TRIG, GPIO.LOW)

# Measure echo
while GPIO.input(ECHO) == 0:
    pulse_start = time.time()
    
while GPIO.input(ECHO) == 1:
    pulse_end = time.time()

distance = (pulse_end - pulse_start) * 17150
print(f"Distance: {distance} cm")
```

## Software Issues

### "GEMINI_API_KEY not set"

**Solution:**
```bash
# Create .env file
cp .env.example .env

# Edit .env
nano .env

# Add your key:
GEMINI_API_KEY=your_actual_key_here
```

Get key from: https://ai.google.dev/

### "ModuleNotFoundError"

**Cause:** Missing Python package.

**Solution:**
```bash
# Reinstall requirements
pip install -r requirements.txt

# For specific module
pip install <module_name>
```

### "Configuration file not found"

**Cause:** Running from wrong directory.

**Solution:**
```bash
# Run from correct directory
cd pc_server
python3 main.py

# OR from project root
cd distributed-robot-system
python3 pc_server/main.py
```

### AI Not Responding

**Check 1: API Key Valid**
```bash
# Test API key
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     -H "x-goog-api-key: YOUR_API_KEY" \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
```

**Check 2: Rate Limits**
Wait a few minutes if you hit API limits.

**Check 3: Internet Connection**
```bash
ping 8.8.8.8
```

### Face Animation Not Showing

**Check 1: Display Module Running**
Verify Pi client is connected and display initialized.

**Check 2: Display Configuration**
Check `config/robot_config.yaml`:
```yaml
display:
  width: 1280
  height: 800
  fullscreen: true
```

**Check 3: X11 Forwarding**
If running over SSH:
```bash
ssh -X pi@YOUR_PI_IP
```

## Performance Issues

### High Latency

**Solution 1: Reduce Camera Resolution**
```yaml
camera:
  width: 320  # Lower from 640
  height: 240  # Lower from 480
```

**Solution 2: Reduce Frame Rate**
```yaml
camera:
  fps: 15  # Lower from 30
```

**Solution 3: Use Wired Connection**
Ethernet instead of WiFi for better stability.

### High CPU Usage

**Check 1: Monitoring**
```bash
top
htop  # Better interface
```

**Solution 1: Disable Unused Features**
```yaml
lidar:
  enabled: false  # If not using

camera:
  fps: 10  # Reduce frame rate
```

**Solution 2: Optimize OpenCV**
Use `opencv-python-headless` for lower overhead.

### Memory Issues

**Check Memory Usage:**
```bash
free -h
```

**Solution: Add Swap**
```bash
# On Pi
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE to 2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Getting Help

If you can't resolve your issue:

1. **Check logs:**
   ```bash
   tail -f logs/robot.log
   ```

2. **Enable debug mode:**
   ```bash
   # In .env
   LOG_LEVEL=DEBUG
   FLASK_DEBUG=True
   ```

3. **Create GitHub issue:**
   - Go to: https://github.com/vivan129/distributed-robot-system/issues
   - Include:
     - Error message
     - Log output
     - System info (OS, Python version)
     - Steps to reproduce

4. **Community support:**
   - Check existing issues
   - Ask in discussions
   - Provide detailed information

---

**Last Updated:** January 2026