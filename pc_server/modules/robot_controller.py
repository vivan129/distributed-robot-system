#!/usr/bin/env python3
"""
Robot Controller Module

Handles sending commands to the Raspberry Pi client via SocketIO.
"""

import logging
import asyncio
from typing import Dict, Optional
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


class RobotController:
    """Controller for sending commands to Raspberry Pi."""
    
    def __init__(self, config: dict, socketio: SocketIO):
        """
        Initialize robot controller.
        
        Args:
            config: Robot configuration dictionary
            socketio: Flask-SocketIO instance
        """
        self.config = config
        self.socketio = socketio
        self.pi_sid = None  # Pi client session ID
        self.pi_connected = False
        
        logger.info("Robot controller initialized")
    
    def set_pi_connection(self, sid: Optional[str], connected: bool):
        """
        Set Pi connection status.
        
        Args:
            sid: Session ID of Pi client
            connected: Connection status
        """
        self.pi_sid = sid
        self.pi_connected = connected
        logger.info(f"Pi connection: {connected} (SID: {sid})")
    
    async def send_movement(self, command: Dict) -> bool:
        """
        Send movement command to Pi.
        
        Args:
            command: Movement command dict with 'direction' and 'duration'
            
        Returns:
            True if command sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send movement: Pi not connected")
            return False
        
        try:
            # FIXED: Use 'movement_command' event name
            self.socketio.emit(
                'movement_command',
                command,
                namespace='/pi',
                to=self.pi_sid
            )
            logger.info(f"Sent movement command: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending movement command: {e}")
            return False
    
    async def send_stop(self) -> bool:
        """
        Send emergency stop command to Pi.
        
        Returns:
            True if command sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send stop: Pi not connected")
            return False
        
        try:
            # FIXED: Use 'stop_command' event name
            self.socketio.emit(
                'stop_command',
                {},
                namespace='/pi',
                to=self.pi_sid
            )
            logger.info("Sent stop command")
            return True
            
        except Exception as e:
            logger.error(f"Error sending stop command: {e}")
            return False
    
    async def send_face_animation(self, animation_data: Dict, duration: float) -> bool:
        """
        Send face animation to Pi display.
        
        Args:
            animation_data: Animation keyframes
            duration: Animation duration in seconds
            
        Returns:
            True if command sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send animation: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'face_animation',
                {
                    'animation': animation_data,
                    'duration': duration
                },
                namespace='/pi',
                to=self.pi_sid
            )
            logger.info(f"Sent face animation (duration: {duration}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error sending face animation: {e}")
            return False
    
    async def send_audio(self, audio_path: str) -> bool:
        """
        Send audio to Pi for playback.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if audio sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send audio: Pi not connected")
            return False
        
        try:
            import base64
            
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Encode to base64
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # FIXED: Use 'play_audio' event name and 'audio_data' key
            self.socketio.emit(
                'play_audio',
                {'audio_data': audio_base64},
                namespace='/pi',
                to=self.pi_sid
            )
            logger.info(f"Sent audio: {audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            return False
    
    def get_status(self) -> Dict:
        """
        Get robot connection status.
        
        Returns:
            Status dictionary
        """
        return {
            'pi_connected': self.pi_connected,
            'pi_sid': self.pi_sid
        }


if __name__ == "__main__":
    # Test the controller
    import yaml
    from flask import Flask
    from flask_socketio import SocketIO
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create Flask app
    app = Flask(__name__)
    socketio = SocketIO(app)
    
    # Initialize controller
    controller = RobotController(config, socketio)
    
    print("\n" + "="*60)
    print("ROBOT CONTROLLER TEST")
    print("="*60 + "\n")
    
    # Test commands
    async def test():
        # Simulate Pi connection
        controller.set_pi_connection('test-sid', True)
        
        # Test movement
        await controller.send_movement({'direction': 'forward', 'duration': 2.0})
        
        # Test stop
        await controller.send_stop()
        
        # Get status
        status = controller.get_status()
        print(f"\nController status: {status}")
    
    asyncio.run(test())
