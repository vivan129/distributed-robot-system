#!/usr/bin/env python3
"""
Raspberry Pi Client - Hardware Interface
Handles motors, camera, sensors, and display
"""

import sys
import os

# Check Python version
if sys.version_info < (3, 9):
    print("❌ ERROR: Python 3.9 or higher is required!")
    print(f"   Current version: {sys.version}")
    print("\nPlease upgrade Python on Raspberry Pi:")
    print("  sudo apt update")
    print("  sudo apt install python3.9 python3.9-venv")
    sys.exit(1)

print(f"✅ Python version: {sys.version.split()[0]}")
print("🤖 Starting Raspberry Pi Client...")
print("="*60)

# Import remaining modules after version check
import logging
import time
from pathlib import Path
import yaml
import socketio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logs directory
log_dir = Path('../logs')
log_dir.mkdir(exist_ok=True)

# Setup logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config
try:
    with open('../config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    logger.info("✅ Configuration loaded")
except FileNotFoundError:
    logger.error("❌ Configuration file not found: ../config/robot_config.yaml")
    sys.exit(1)

# Check if running on Raspberry Pi
skip_hardware = os.getenv('SKIP_HARDWARE_INIT', 'False').lower() == 'true'

try:
    if not skip_hardware:
        from hardware.motor_controller import MotorController
        from hardware.camera_module import CameraModule
        from hardware.lidar_module import LidarModule
        from display.face_display import FaceDisplay
        logger.info("✅ Hardware modules imported")
    else:
        logger.warning("⚠️  Hardware initialization skipped (SKIP_HARDWARE_INIT=True)")
except ImportError as e:
    if 'RPi.GPIO' in str(e):
        logger.error("❌ RPi.GPIO not available - are you running on a Raspberry Pi?")
        logger.error("   For development on PC, set SKIP_HARDWARE_INIT=True in .env")
    else:
        logger.error(f"❌ Failed to import hardware modules: {e}")
    sys.exit(1)

# Initialize SocketIO client
sio = socketio.Client()
network_config = config.get('network', {})
pc_server_url = f"http://{network_config.get('pc_ip')}:{network_config.get('pc_port')}"

logger.info(f"🌐 Connecting to PC server: {pc_server_url}")

# Initialize hardware (if not skipped)
if not skip_hardware:
    try:
        motors = MotorController(config)
        camera = CameraModule(config)
        lidar = LidarModule(config) if config.get('lidar', {}).get('enabled', False) else None
        display = FaceDisplay(config)
        logger.info("✅ Hardware initialized")
    except Exception as e:
        logger.error(f"❌ Hardware initialization failed: {e}")
        sys.exit(1)


# SocketIO event handlers
@sio.event
def connect():
    logger.info("✅ Connected to PC server")
    sio.emit('pi_connected', {'status': 'ready'}, namespace='/pi')


@sio.event
def disconnect():
    logger.warning("⚠️  Disconnected from PC server")
    if not skip_hardware:
        motors.stop()


@sio.on('movement', namespace='/pi')
def handle_movement(data):
    """Execute movement command"""
    if skip_hardware:
        logger.info(f"[SIMULATION] Movement: {data}")
        return
        
    try:
        direction = data.get('direction')
        duration = data.get('duration', 2.0)
        
        logger.info(f"Moving {direction} for {duration}s")
        
        if direction == 'forward':
            motors.forward()
        elif direction == 'backward':
            motors.backward()
        elif direction == 'left':
            motors.turn_left()
        elif direction == 'right':
            motors.turn_right()
        elif direction == 'stop':
            motors.stop()
            
        if direction != 'stop':
            time.sleep(duration)
            motors.stop()
            
        sio.emit('movement_complete', {'direction': direction, 'duration': duration}, namespace='/pi')
        
    except Exception as e:
        logger.error(f"Movement error: {e}")


@sio.on('stop', namespace='/pi')
def handle_stop(data):
    """Emergency stop"""
    if not skip_hardware:
        motors.stop()
    logger.info("🛑 Emergency stop")
    sio.emit('stop_complete', {}, namespace='/pi')


@sio.on('face_animation', namespace='/pi')
def handle_face_animation(data):
    """Display face animation"""
    if skip_hardware:
        logger.info("[SIMULATION] Face animation received")
        return
        
    try:
        animation_data = data.get('animation')
        duration = data.get('duration', 2.0)
        display.play_animation(animation_data, duration)
    except Exception as e:
        logger.error(f"Face animation error: {e}")


@sio.on('audio', namespace='/pi')
def handle_audio(data):
    """Play audio"""
    if skip_hardware:
        logger.info("[SIMULATION] Audio received")
        return
        
    try:
        audio_data = data.get('audio')
        # TODO: Implement audio playback
        logger.info("Playing audio...")
    except Exception as e:
        logger.error(f"Audio playback error: {e}")


def camera_stream():
    """Stream camera frames to PC"""
    if skip_hardware:
        return
        
    while True:
        try:
            frame = camera.get_frame()
            if frame is not None:
                sio.emit('camera_frame', {'frame': frame}, namespace='/pi')
            time.sleep(0.033)  # ~30 FPS
        except Exception as e:
            logger.error(f"Camera stream error: {e}")
            time.sleep(1)


def lidar_stream():
    """Stream LiDAR data to PC"""
    if skip_hardware or lidar is None:
        return
        
    while True:
        try:
            scan_data = lidar.get_scan()
            if scan_data:
                sio.emit('lidar_scan', scan_data, namespace='/pi')
            time.sleep(0.1)  # 10 Hz
        except Exception as e:
            logger.error(f"LiDAR stream error: {e}")
            time.sleep(1)


if __name__ == '__main__':
    try:
        # Connect to PC server
        sio.connect(pc_server_url, namespaces=['/pi'])
        
        logger.info("="*60)
        logger.info("✅ Raspberry Pi client running")
        logger.info(f"🔗 Connected to: {pc_server_url}")
        logger.info("="*60)
        
        # Start streaming (in separate threads if needed)
        # For now, just keep the connection alive
        sio.wait()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        if not skip_hardware:
            motors.cleanup()
        sio.disconnect()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        if not skip_hardware:
            motors.cleanup()
        sys.exit(1)
