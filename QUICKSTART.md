# 🚀 Quick Start Guide

Get your robot running in 15 minutes!

## 📋 Prerequisites

### Hardware
- **PC**: Ubuntu 20.04+ with 8GB RAM
- **Raspberry Pi**: 3B+ or 4 with Raspbian OS
- **Network**: Both on same WiFi/LAN

### Software
- Python 3.8+
- Git
- Google Gemini API key ([Get one free](https://ai.google.dev/))

---

## 🖥️ Step 1: Setup PC Server (5 minutes)

### 1.1 Clone Repository
```bash
git clone https://github.com/vivan129/distributed-robot-system.git
cd distributed-robot-system
```

### 1.2 Run Setup Script
```bash
chmod +x scripts/setup_pc.sh
./scripts/setup_pc.sh
```

### 1.3 Configure Environment
```bash
cp .env.example .env
nano .env
```

Add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 1.4 Update Network Config
```bash
nano config/robot_config.yaml
```

Find your PC's IP:
```bash
hostname -I
```

Update these lines:
```yaml
network:
  pc_ip: "192.168.1.100"  # YOUR PC IP HERE
  pi_ip: "192.168.1.101"  # YOUR PI IP HERE
```

### 1.5 Verify Setup
```bash
python scripts/verify_setup.py
```

### 1.6 Start Server
```bash
cd pc_server
source venv/bin/activate
python main.py
```

You should see:
```
============================================================
🖥️  ROBOT PC SERVER STARTING
============================================================
✓ Gemini AI connected
✓ TTS engine initialized
🌐 Dashboard: http://192.168.1.100:5000
============================================================
```

**✅ Keep this terminal open!**

---

## 🤖 Step 2: Setup Raspberry Pi (5 minutes)

### 2.1 SSH into Pi
```bash
ssh pi@raspberrypi.local
# or
ssh pi@192.168.1.101
```

### 2.2 Clone Repository on Pi
```bash
git clone https://github.com/vivan129/distributed-robot-system.git
cd distributed-robot-system
```

### 2.3 Run Setup Script
```bash
chmod +x scripts/setup_pi.sh
./scripts/setup_pi.sh
```

**Important**: Log out and back in after setup for group permissions to take effect:
```bash
logout
# SSH back in
ssh pi@raspberrypi.local
cd distributed-robot-system
```

### 2.4 Connect Hardware (If Available)

**Motors** (optional for testing):
- L1 → GPIO 33 (Pin 33)
- L2 → GPIO 38 (Pin 38)
- R1 → GPIO 35 (Pin 35)
- R2 → GPIO 40 (Pin 40)

**Camera** (optional):
- Pi Camera or USB webcam

**LiDAR** (optional):
- RP-LIDAR A1 → USB port

### 2.5 Start Client
```bash
cd pi_client
source venv/bin/activate
python main.py
```

You should see:
```
============================================================
🤖 RASPBERRY PI CLIENT STARTING
============================================================
✓ Motors initialized
✓ Camera ready
✓ Connected to PC: http://192.168.1.100:5000
============================================================
```

---

## 🎮 Step 3: Test the System (5 minutes)

### 3.1 Open Dashboard

On **any device** on the same network, open browser:
```
http://192.168.1.100:5000
```

You should see the control dashboard!

### 3.2 Test Movement (Software Only)

**Without Hardware**: The motors will initialize but won't move anything. You'll see commands in the Pi terminal.

Click buttons on dashboard:
- **↑ Forward** → Enter duration → Click OK
- **← Left** → Enter duration → Click OK
- **⛔ STOP** → Immediate stop

Check Pi terminal for:
```
Moving forward for 2.0s
Motors stopped
```

### 3.3 Test AI Voice (Software Only)

**Type a command** in the dashboard text box:
```
Move forward for 3 seconds
```

Click **Send**

Watch the logs:
1. ✅ PC recognizes command
2. ✅ Gemini AI processes it
3. ✅ TTS generates response
4. ✅ Pi receives commands

### 3.4 Test Camera (If Connected)

The dashboard should show:
- Live camera feed in "Camera Feed" panel
- Updates when Pi camera is working

### 3.5 Test Sensors (If Connected)

**Ultrasonic Sensor**:
- Wave hand in front of sensor
- Watch "Distance" value change on dashboard
- Get too close → Auto-stop triggered!

**LiDAR**:
- Spin the LiDAR
- Watch "LiDAR Points" counter on dashboard
- See SLAM map building (if configured)

---

## 🎉 Success Checklist

- [ ] PC server running
- [ ] Pi client connected
- [ ] Dashboard accessible
- [ ] Commands work (even without hardware)
- [ ] No error messages in terminals

---

## 🐛 Troubleshooting

### Pi Can't Connect to PC

**Problem**: `Connection refused` error

**Solutions**:
```bash
# 1. Check PC server is running
# 2. Verify IPs are correct
ping 192.168.1.100  # From Pi

# 3. Check firewall on PC
sudo ufw allow 5000/tcp

# 4. Verify same network
# Both devices should have IPs like 192.168.1.x
```

### GPIO Permission Denied

**Problem**: `PermissionError: /dev/gpiomem`

**Solution**:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Log out and back in
logout
# SSH back in
```

### Camera Not Found

**Problem**: `Camera initialization failed`

**Solutions**:
```bash
# Enable camera
sudo raspi-config nonint do_camera 0
sudo reboot

# Test camera
raspistill -o test.jpg

# Or use USB webcam
# Update config to use "opencv" camera type
```

### LiDAR Not Detected

**Problem**: `LiDAR connection failed`

**Solutions**:
```bash
# Check USB connection
ls /dev/ttyUSB*

# Add to dialout group
sudo usermod -a -G dialout $USER
logout
# SSH back in

# Set permissions
sudo chmod 666 /dev/ttyUSB0
```

### Gemini API Error

**Problem**: `API key not found` or `Authentication error`

**Solutions**:
```bash
# 1. Check .env file exists
ls -la .env

# 2. Verify API key is set
cat .env | grep GEMINI

# 3. Get new key at https://ai.google.dev/
```

### Motors Won't Stop

**Problem**: Motors continue running after exit

**Solution**:
```bash
# Emergency cleanup
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup([33,38,35,40], GPIO.OUT)
GPIO.output([33,38,35,40], GPIO.LOW)
GPIO.cleanup()
"

# Or disconnect motor power
```

---

## 📚 Next Steps

### Learn More
- Read full [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to add features
- Explore module documentation in source files

### Customize
- Modify `config/robot_config.yaml` for your hardware
- Adjust AI personality in config
- Change TTS voice settings
- Configure SLAM parameters

### Add Features
- Object detection with YOLO
- Autonomous navigation
- Mobile app control
- Multi-robot coordination

---

## 🆘 Still Need Help?

- 🐛 **Bug**: Open [GitHub Issue](https://github.com/vivan129/distributed-robot-system/issues)
- 💬 **Question**: Start a [Discussion](https://github.com/vivan129/distributed-robot-system/discussions)
- 📖 **Docs**: Check the [Wiki](https://github.com/vivan129/distributed-robot-system/wiki)

---

**🎊 Congratulations!** Your distributed robot system is running!

Now let's build something amazing! 🤖✨