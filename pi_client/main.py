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

import logging
import time
import threading
import base64
import tempfile
import subprocess
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
        from hardware.ultrasonic_sensor import UltrasonicSensor
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
sio = socketio.Client(reconnection=True, reconnection_delay=2)
network_config = config.get('network', {})
pc_server_url = f"http://{network_config.get('pc_ip')}:{network_config.get('pc_port')}"

logger.info(f"🌐 Connecting to PC server: {pc_server_url}")

# Initialize hardware (if not skipped)
motors = None
camera = None
lidar = None
display = None
ultrasonic = None

if not skip_hardware:
    try:
        motors = MotorController(config)
        camera = CameraModule(config)
        
        # LiDAR (optional)
        if config.get('lidar', {}).get('enabled', False):
            try:
                lidar = LidarModule(config)
                logger.info("✅ LiDAR initialized")
            except Exception as e:
                logger.warning(f"⚠️  LiDAR initialization failed: {e}")
                lidar = None
        
        # Ultrasonic sensor (optional)
        if config.get('ultrasonic', {}).get('enabled', False):
            try:
                ultrasonic = UltrasonicSensor(config)
                logger.info("✅ Ultrasonic sensor initialized")
            except Exception as e:
                logger.warning(f"⚠️  Ultrasonic initialization failed: {e}")
                ultrasonic = None
        
        # Face display
        try:
            display = FaceDisplay(config)
            logger.info("✅ Face display initialized")
        except Exception as e:
            logger.warning(f"⚠️  Face display initialization failed: {e}")
            display = None
            
        logger.info("✅ Hardware initialized")
    except Exception as e:
        logger.error(f"❌ Hardware initialization failed: {e}")
        sys.exit(1)


# ============================================================================
# SOCKETIO EVENT HANDLERS
# ============================================================================

@sio.event
def connect():
    """Handle connection to PC server."""
    logger.info("✅ Connected to PC server")
    sio.emit('pi_connected', {'status': 'ready'}, namespace='/pi')


@sio.event
def disconnect():
    """Handle disconnection from PC server."""
    logger.warning("⚠️  Disconnected from PC server")
    if motors and not skip_hardware:
        motors.stop()


@sio.on('movement_command', namespace='/pi')  # FIXED: Changed from 'movement'
def handle_movement(data):
    """
    Execute movement command.
    
    Data format:
    {
        'direction': 'forward'|'backward'|'left'|'right'|'stop',
        'duration': float (seconds)
    }
    """
    if skip_hardware:
        logger.info(f"[SIMULATION] Movement: {data}")
        return
        
    try:
        direction = data.get('direction')
        duration = data.get('duration', 2.0)
        
        logger.info(f"Moving {direction} for {duration}s")
        
        if direction == 'stop':
            motors.stop()
        else:
            # FIXED: Use unified move() method
            motors.move(direction, duration)
            
        sio.emit('movement_complete', {
            'direction': direction,
            'duration': duration
        }, namespace='/pi')
        
    except Exception as e:
        logger.error(f"Movement error: {e}", exc_info=True)


@sio.on('stop_command', namespace='/pi')  # FIXED: Changed from 'stop'
def handle_stop(data):
    """Emergency stop."""
    if not skip_hardware and motors:
        motors.stop()
    logger.info("🛑 Emergency stop")
    sio.emit('stop_complete', {}, namespace='/pi')


@sio.on('face_animation', namespace='/pi')
def handle_face_animation(data):
    """
    Display face animation.
    
    Data format:
    {
        'animation': {...},  # Animation keyframes
        'duration': float
    }
    """
    if skip_hardware or not display:
        logger.info("[SIMULATION] Face animation received")
        return
        
    try:
        animation_data = data.get('animation')
        duration = data.get('duration', 2.0)
        
        # FIXED: Use update_animation() method
        display.update_animation({
            'type': 'lipsync',
            'keyframes': animation_data.get('keyframes', []),
            'duration': duration
        })
        
        logger.info(f"Playing face animation (duration: {duration}s)")
        
    except Exception as e:
        logger.error(f"Face animation error: {e}", exc_info=True)


@sio.on('play_audio', namespace='/pi')  # FIXED: Changed from 'audio'
def handle_audio(data):
    """
    Play audio on Pi speakers.
    
    Data format:
    {
        'audio_data': base64-encoded MP3 audio
    }
    """
    if skip_hardware:
        logger.info("[SIMULATION] Audio received")
        return
        
    try:
        audio_base64 = data.get('audio_data')
        if not audio_base64:
            logger.error("No audio data received")
            return
            
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name
        
        # Play with mpg123 (install: sudo apt install mpg123)
        logger.info("Playing audio...")
        subprocess.run(['mpg123', '-q', audio_path], check=False)
        
        # Clean up
        os.remove(audio_path)
        logger.info("Audio playback complete")
        
    except FileNotFoundError:
        logger.error("mpg123 not installed. Install with: sudo apt install mpg123")
    except Exception as e:
        logger.error(f"Audio playback error: {e}", exc_info=True)


# ============================================================================
# STREAMING THREADS
# ============================================================================

def camera_stream():
    """Stream camera frames to PC."""
    if skip_hardware or not camera:
        return
        
    logger.info("📷 Camera stream started")
    
    while True:
        try:
            if not sio.connected:
                time.sleep(1)
                continue
                
            frame = camera.get_frame()
            if frame:
                sio.emit('camera_frame', {'frame': frame}, namespace='/pi')
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            logger.error(f"Camera stream error: {e}")
            time.sleep(1)


def lidar_stream():
    """Stream LiDAR data to PC."""
    if skip_hardware or not lidar:
        return
        
    logger.info("📡 LiDAR stream started")
    
    while True:
        try:
            if not sio.connected:
                time.sleep(1)
                continue
                
            scan_data = lidar.get_scan()
            if scan_data:
                sio.emit('lidar_scan', scan_data, namespace='/pi')
            time.sleep(0.1)  # 10 Hz
            
        except Exception as e:
            logger.error(f"LiDAR stream error: {e}")
            time.sleep(1)


def ultrasonic_monitor():
    """Monitor ultrasonic sensor for obstacles."""
    if skip_hardware or not ultrasonic:
        return
        
    logger.info("🔊 Ultrasonic monitor started")
    
    safety_config = config.get('safety', {})
    threshold = safety_config.get('obstacle_threshold', 30)  # cm
    
    while True:
        try:
            if not sio.connected:
                time.sleep(1)
                continue
                
            distance = ultrasonic.get_average_distance()
            
            # Send distance data
            sio.emit('ultrasonic_data', {'distance': distance}, namespace='/pi')
            
            # Check for obstacles
            if distance < threshold and motors and motors.is_moving:
                logger.warning(f"⚠️  Obstacle detected at {distance}cm - stopping!")
                motors.stop()
                sio.emit('obstacle_alert', {'distance': distance}, namespace='/pi')
            
            time.sleep(0.1)  # 10 Hz
            
        except Exception as e:
            logger.error(f"Ultrasonic monitor error: {e}")
            time.sleep(1)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    try:
        # Connect to PC server
        logger.info(f"Connecting to {pc_server_url}...")
        sio.connect(pc_server_url, namespaces=['/pi'])
        
        logger.info("="*60)
        logger.info("✅ Raspberry Pi client running")
        logger.info(f"🔗 Connected to: {pc_server_url}")
        logger.info("="*60)
        
        # Start streaming threads
        threads = []
        
        if camera and not skip_hardware:
            camera_thread = threading.Thread(target=camera_stream, daemon=True)
            camera_thread.start()
            threads.append(camera_thread)
            logger.info("📷 Camera thread started")
        
        if lidar and not skip_hardware:
            lidar_thread = threading.Thread(target=lidar_stream, daemon=True)
            lidar_thread.start()
            threads.append(lidar_thread)
            logger.info("📡 LiDAR thread started")
        
        if ultrasonic and not skip_hardware:
            ultrasonic_thread = threading.Thread(target=ultrasonic_monitor, daemon=True)
            ultrasonic_thread.start()
            threads.append(ultrasonic_thread)
            logger.info("🔊 Ultrasonic thread started")
        
        # Keep the connection alive
        sio.wait()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        
    finally:
        # Cleanup
        if motors and not skip_hardware:
            motors.cleanup()
            logger.info("Motors cleaned up")
        
        if camera and not skip_hardware:
            camera.release()
            logger.info("Camera released")
        
        if lidar and not skip_hardware:
            lidar.stop()
            logger.info("LiDAR stopped")
        
        if sio.connected:
            sio.disconnect()
            logger.info("Disconnected from server")
        
        logger.info("Shutdown complete")
        sys.exit(0)
