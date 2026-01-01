"""
Raspberry Pi Client - Hardware Interface Only
No heavy processing - just I/O streaming to PC
"""

import asyncio
import logging
import time
from flask import Flask, render_template
from flask_socketio import SocketIO
import socketio as sio_client
import yaml

from hardware.motor_controller import MotorController
from hardware.camera_streamer import CameraStreamer
from hardware.lidar_streamer import LiDARStreamer
from hardware.ultrasonic import UltrasonicSensor
from hardware.audio_io import AudioIO

# Load config
with open('../config/robot_config.yaml') as f:
    config = yaml.safe_load(f)

# Local display server (for 10.1" screen)
app = Flask(__name__)
socketio_local = SocketIO(app, cors_allowed_origins="*")

# Client to PC server
pc_client = sio_client.Client()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PiClient:
    def __init__(self):
        # Initialize hardware
        self.motors = MotorController(config)
        self.camera = CameraStreamer(config)
        self.lidar = LiDARStreamer(config)
        self.ultrasonic = UltrasonicSensor(config)
        self.audio = AudioIO(config)
        
        self.pc_connected = False
        
    async def connect_to_pc(self):
        """Connect to PC server"""
        try:
            pc_url = f"http://{config['pc_ip']}:{config['pc_port']}"
            await pc_client.connect(pc_url, namespaces=['/pi'])
            self.pc_connected = True
            logger.info(f"✓ Connected to PC: {pc_url}")
        except Exception as e:
            logger.error(f"✗ PC connection failed: {e}")
            
    async def stream_camera(self):
        """Stream camera to PC"""
        async for frame in self.camera.stream():
            if self.pc_connected:
                await pc_client.emit('camera_frame', {
                    'frame': frame,
                    'timestamp': time.time()
                }, namespace='/pi')
                
    async def stream_lidar(self):
        """Stream LiDAR to PC"""
        async for scan in self.lidar.stream():
            if self.pc_connected:
                await pc_client.emit('lidar_scan', {
                    'ranges': scan['ranges'],
                    'angles': scan['angles'],
                    'timestamp': time.time()
                }, namespace='/pi')
                
    async def monitor_ultrasonic(self):
        """Send ultrasonic readings"""
        while True:
            distance = self.ultrasonic.get_distance()
            if self.pc_connected:
                await pc_client.emit('ultrasonic_data', {
                    'distance': distance
                }, namespace='/pi')
            await asyncio.sleep(0.1)
            
    async def stream_microphone(self):
        """Stream mic audio to PC"""
        async for audio_chunk in self.audio.stream_input():
            if self.pc_connected:
                await pc_client.emit('mic_audio', {
                    'audio': audio_chunk
                }, namespace='/pi')


client = PiClient()


# ============================================================================
# PC SERVER EVENTS (Receiving commands)
# ============================================================================

@pc_client.on('movement_command', namespace='/pi')
async def handle_movement(data):
    """Execute movement from PC"""
    direction = data['direction']
    duration = data.get('duration', 0)
    
    if duration > 0:
        await client.motors.move_timed(direction, duration)
    else:
        client.motors.move(direction)


@pc_client.on('stop_command', namespace='/pi')
def handle_stop(data):
    """Emergency stop"""
    client.motors.stop()


@pc_client.on('face_animation', namespace='/pi')
def handle_face(data):
    """Receive face animation from PC - forward to local display"""
    socketio_local.emit('render_face', data)


@pc_client.on('play_audio', namespace='/pi')
async def handle_audio(data):
    """Play TTS audio on speakers"""
    await client.audio.play(data['audio_data'])


# ============================================================================
# LOCAL DISPLAY SERVER (for 10.1" screen)
# ============================================================================

@app.route('/')
def face_display():
    """Full-screen face animation"""
    return render_template('face.html')


@socketio_local.on('connect')
def display_connect():
    logger.info("Local display connected")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    logger.info("="*60)
    logger.info("🤖 RASPBERRY PI CLIENT STARTING")
    logger.info("="*60)
    logger.info(f"📷 Camera: {config['camera_type']}")
    logger.info(f"🔵 LiDAR: RP-LIDAR A1")
    logger.info(f"🖥️  Display: http://localhost:{config['pi_display_port']}")
    logger.info("="*60)
    
    # Connect to PC
    await client.connect_to_pc()
    
    # Start all streaming tasks
    await asyncio.gather(
        client.stream_camera(),
        client.stream_lidar(),
        client.monitor_ultrasonic(),
        client.stream_microphone(),
        socketio_local.run_async(app, host='0.0.0.0', port=config['pi_display_port'])
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Shutting down...")
        client.motors.stop()
        client.motors.cleanup()
