"""
Robot Controller Module
Sends commands to Raspberry Pi hardware
"""

import logging
import base64

logger = logging.getLogger(__name__)


class RobotController:
    """
    Interface for sending commands to Pi client
    """
    
    def __init__(self, config, socketio):
        self.config = config
        self.socketio = socketio
        logger.info("✓ Robot controller initialized")
        
    async def send_movement(self, movement_cmd):
        """
        Send movement command to Pi
        
        Args:
            movement_cmd: {'direction': 'forward', 'duration': 3}
        """
        try:
            self.socketio.emit('movement_command', movement_cmd, namespace='/pi')
            logger.info(f"Movement sent: {movement_cmd}")
        except Exception as e:
            logger.error(f"Movement send error: {e}")
            
    def send_stop(self):
        """
        Emergency stop command
        """
        try:
            self.socketio.emit('stop_command', {}, namespace='/pi')
            logger.warning("EMERGENCY STOP sent")
        except Exception as e:
            logger.error(f"Stop send error: {e}")
            
    async def send_audio(self, audio_path):
        """
        Send audio file to Pi for playback
        
        Args:
            audio_path: Path to audio file
        """
        try:
            with open(audio_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
                
            self.socketio.emit('play_audio', {'audio_data': audio_data}, namespace='/pi')
            logger.info(f"Audio sent: {audio_path}")
        except Exception as e:
            logger.error(f"Audio send error: {e}")
