#!/usr/bin/env python3
"""
Robot Controller Module - Centralized Command Dispatcher

Coordinates all robot subsystems and manages communication
with Raspberry Pi hardware interface.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import asyncio
from typing import Dict, Optional, Callable
import time

logger = logging.getLogger(__name__)


class RobotController:
    """Central controller for robot command coordination."""
    
    def __init__(self, config: Dict, socketio):
        """
        Initialize robot controller.
        
        Args:
            config: Robot configuration dictionary
            socketio: SocketIO instance for communication
        """
        self.config = config
        self.socketio = socketio
        
        # Connection state
        self.pi_connected = False
        self.pi_sid = None
        
        # Command queue
        self.command_queue = asyncio.Queue()
        
        # State tracking
        self.current_state = {
            'moving': False,
            'direction': None,
            'last_command': None,
            'last_command_time': 0
        }
        
        # Sensor data
        self.sensor_data = {
            'camera_frame': None,
            'lidar_scan': None,
            'ultrasonic_distance': None,
            'last_update': 0
        }
        
        logger.info("Robot Controller initialized")
    
    def set_pi_connection(self, sid: str, connected: bool):
        """
        Update Pi connection status.
        
        Args:
            sid: Socket ID
            connected: Connection status
        """
        self.pi_connected = connected
        self.pi_sid = sid if connected else None
        
        status = "connected" if connected else "disconnected"
        logger.info(f"Raspberry Pi {status} (sid: {sid})")
    
    async def send_movement_command(self, command: Dict):
        """
        Send movement command to Pi.
        
        Args:
            command: Movement command dictionary
                - direction: forward, backward, left, right, stop
                - duration: seconds (optional)
                - speed: 0-100 (optional)
        """
        if not self.pi_connected:
            logger.warning("Cannot send command - Pi not connected")
            return False
        
        try:
            # Validate command
            if 'direction' not in command:
                logger.error("Movement command missing 'direction'")
                return False
            
            # Set defaults
            command.setdefault('duration', 2.0)
            command.setdefault('speed', 75)
            
            # Send to Pi
            self.socketio.emit(
                'movement_command',
                command,
                room=self.pi_sid,
                namespace='/pi'
            )
            
            # Update state
            self.current_state['moving'] = True
            self.current_state['direction'] = command['direction']
            self.current_state['last_command'] = command
            self.current_state['last_command_time'] = time.time()
            
            logger.info(f"Movement command sent: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send movement command: {e}")
            return False
    
    async def send_stop_command(self):
        """
        Send emergency stop command to Pi.
        """
        if not self.pi_connected:
            logger.warning("Cannot send stop - Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'stop_command',
                {},
                room=self.pi_sid,
                namespace='/pi'
            )
            
            self.current_state['moving'] = False
            self.current_state['direction'] = None
            
            logger.info("Stop command sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send stop command: {e}")
            return False
    
    async def send_face_animation(self, keyframes: list, duration: float):
        """
        Send face animation to Pi display.
        
        Args:
            keyframes: List of animation keyframe dictionaries
            duration: Total animation duration (seconds)
        """
        if not self.pi_connected:
            logger.warning("Cannot send animation - Pi not connected")
            return False
        
        try:
            animation_data = {
                'keyframes': keyframes,
                'duration': duration,
                'fps': self.config.get('display', {}).get('fps', 60)
            }
            
            self.socketio.emit(
                'face_animation',
                animation_data,
                room=self.pi_sid,
                namespace='/pi'
            )
            
            logger.debug(f"Face animation sent ({len(keyframes)} keyframes, {duration:.2f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send face animation: {e}")
            return False
    
    async def send_audio(self, audio_path: str):
        """
        Send audio file path to Pi for playback.
        
        Args:
            audio_path: Path to audio file
        """
        if not self.pi_connected:
            logger.warning("Cannot send audio - Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'play_audio',
                {'audio_path': audio_path},
                room=self.pi_sid,
                namespace='/pi'
            )
            
            logger.info(f"Audio playback requested: {audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio command: {e}")
            return False
    
    def update_camera_frame(self, frame_data: bytes, timestamp: float):
        """
        Update camera frame from Pi.
        
        Args:
            frame_data: JPEG frame data
            timestamp: Frame timestamp
        """
        self.sensor_data['camera_frame'] = frame_data
        self.sensor_data['last_update'] = timestamp
    
    def update_lidar_scan(self, scan_data: Dict):
        """
        Update LiDAR scan from Pi.
        
        Args:
            scan_data: Dictionary with ranges and angles
        """
        self.sensor_data['lidar_scan'] = scan_data
        self.sensor_data['last_update'] = time.time()
    
    def update_ultrasonic(self, distance: float):
        """
        Update ultrasonic distance measurement.
        
        Args:
            distance: Distance in cm
        """
        self.sensor_data['ultrasonic_distance'] = distance
        self.sensor_data['last_update'] = time.time()
        
        # Check for obstacles
        threshold = self.config.get('ultrasonic', {}).get('obstacle_threshold', 30)
        if distance < threshold:
            logger.warning(f"Obstacle detected at {distance:.1f}cm!")
            # Could trigger emergency stop here
    
    def get_sensor_data(self) -> Dict:
        """Get latest sensor data."""
        return self.sensor_data.copy()
    
    def get_robot_state(self) -> Dict:
        """Get current robot state."""
        return {
            **self.current_state,
            'pi_connected': self.pi_connected,
            'sensor_age': time.time() - self.sensor_data['last_update']
        }
    
    def is_pi_connected(self) -> bool:
        """Check if Pi is connected."""
        return self.pi_connected


if __name__ == "__main__":
    # Test controller (requires socketio mock)
    logging.basicConfig(level=logging.INFO)
    
    class MockSocketIO:
        def emit(self, event, data, room=None, namespace=None):
            print(f"Mock emit: {event} -> {data}")
    
    import yaml
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    controller = RobotController(config, MockSocketIO())
    
    # Simulate Pi connection
    controller.set_pi_connection("test_sid_123", True)
    
    # Test commands
    asyncio.run(controller.send_movement_command({
        'direction': 'forward',
        'duration': 3.0
    }))
    
    asyncio.run(controller.send_stop_command())
    
    print("\nRobot state:", controller.get_robot_state())
