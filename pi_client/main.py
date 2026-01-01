#!/usr/bin/env python3
"""
Raspberry Pi Client - Main Entry Point

Connects to PC server and handles hardware I/O:
- Motor control
- Camera streaming  
- LiDAR streaming
- Ultrasonic sensing
- Face display
- Audio playback
"""

import os
import sys
import logging
import yaml
import asyncio
import socketio
import signal
import base64
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hardware.motor_controller import MotorController
from hardware.camera_streamer import CameraStreamer
from hardware.lidar_streamer import LiDARStreamer
from hardware.ultrasonic_sensor import UltrasonicSensor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RobotPiClient:
    """Raspberry Pi robot client."""
    
    def __init__(self, config_path: str = '../config/robot_config.yaml'):
        """Initialize Pi client."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Network config
        network = self.config['network']
        self.pc_url = f"http://{network['pc_ip']}:{network['pc_port']}"
        
        # Initialize hardware
        logger.info("Initializing hardware...")
        self.motors = MotorController(self.config)
        self.camera = CameraStreamer(self.config)
        
        try:
            self.lidar = LiDARStreamer(self.config)
        except Exception as e:
            logger.warning(f"LiDAR initialization failed: {e}")
            self.lidar = None
        
        try:
            self.ultrasonic = UltrasonicSensor(self.config)
        except Exception as e:
            logger.warning(f"Ultrasonic sensor initialization failed: {e}")
            self.ultrasonic = None
        
        # SocketIO client
        self.sio = socketio.AsyncClient()
        self._setup_socketio_events()
        
        # State
        self.connected = False
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.running = False
        self.motors.stop()
    
    def _setup_socketio_events(self):
        """Setup SocketIO event handlers."""
        
        @self.sio.event
        async def connect():
            logger.info(f"Connected to PC: {self.pc_url}")
            self.connected = True
            await self.sio.emit('pi_connected', {'status': 'ready'})
        
        @self.sio.event
        async def disconnect():
            logger.info("Disconnected from PC")
            self.connected = False
            self.motors.stop()
        
        @self.sio.on('movement_command')
        async def handle_movement(data):
            """Handle movement command from PC."""
            try:
                direction = data.get('direction')
                duration = data.get('duration', 0)
                
                logger.info(f"Movement command: {direction} for {duration}s")
                self.motors.move(direction, duration)
                
                await self.sio.emit('movement_complete', {'direction': direction})
            
            except Exception as e:
                logger.error(f"Movement error: {e}")
        
        @self.sio.on('stop_command')
        async def handle_stop(data):
            """Handle emergency stop."""
            logger.info("Emergency stop command")
            self.motors.stop()
            await self.sio.emit('stop_complete', {})
        
        @self.sio.on('play_audio')
        async def handle_audio(data):
            """Handle audio playback command."""
            try:
                # Decode audio data
                audio_data = base64.b64decode(data['audio_data'])
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    f.write(audio_data)
                    audio_path = f.name
                
                # Play audio
                os.system(f"mpg123 -q {audio_path} &")
                
                # Cleanup
                os.remove(audio_path)
                
                logger.info("Audio playback started")
            
            except Exception as e:
                logger.error(f"Audio playback error: {e}")
    
    async def stream_camera(self):
        """Stream camera frames to PC."""
        async def send_frame(frame_data):
            if self.connected:
                await self.sio.emit('camera_frame', {'frame': frame_data})
        
        await self.camera.stream_frames(send_frame)
    
    async def stream_lidar(self):
        """Stream LiDAR scans to PC."""
        if not self.lidar:
            return
        
        async def send_scan(scan_data):
            if self.connected:
                await self.sio.emit('lidar_scan', scan_data)
        
        await self.lidar.stream_scans(send_scan)
    
    async def monitor_ultrasonic(self):
        """Monitor ultrasonic sensor."""
        if not self.ultrasonic:
            return
        
        while self.running:
            try:
                distance = self.ultrasonic.measure_distance()
                
                if distance and self.connected:
                    await self.sio.emit('ultrasonic_data', {'distance': distance})
                    
                    # Emergency stop if obstacle too close
                    safety_threshold = self.config.get('safety', {}).get('obstacle_threshold', 30)
                    if distance < safety_threshold and self.motors.is_moving:
                        logger.warning(f"Obstacle detected at {distance}cm, stopping!")
                        self.motors.stop()
                
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Ultrasonic error: {e}")
                await asyncio.sleep(1)
    
    async def run(self):
        """Main run loop."""
        try:
            # Connect to PC
            logger.info(f"Connecting to PC at {self.pc_url}...")
            await self.sio.connect(self.pc_url, namespaces=['/pi'])
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self.stream_camera()),
                asyncio.create_task(self.monitor_ultrasonic())
            ]
            
            if self.lidar:
                tasks.append(asyncio.create_task(self.stream_lidar()))
            
            # Wait for tasks
            await asyncio.gather(*tasks)
        
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up...")
        
        self.motors.cleanup()
        self.camera.release()
        
        if self.lidar:
            self.lidar.release()
        
        logger.info("Cleanup complete")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 RASPBERRY PI CLIENT STARTING")
    print("="*60 + "\n")
    
    try:
        client = RobotPiClient()
        asyncio.run(client.run())
    
    except KeyboardInterrupt:
        print("\n\nShutdown requested...")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
