#!/usr/bin/env python3
"""
Robot Controller Module - Command Dispatcher

Centralized controller for sending commands to Raspberry Pi.
Handles movement, audio playback, and face animation coordination.
"""

import logging
import asyncio
from typing import Dict, Optional
import base64

logger = logging.getLogger(__name__)


class RobotController:
    """Centralized robot command controller."""
    
    def __init__(self, config: dict, socketio):
        """
        Initialize robot controller.
        
        Args:
            config: Configuration dictionary
            socketio: SocketIO instance for communication
        """
        self.config = config
        self.socketio = socketio
        self.pi_connected = False
        self.pi_sid = None
        
        logger.info("Robot controller initialized")
    
    def set_pi_connection(self, sid: str, connected: bool):
        """
        Update Pi connection status.
        
        Args:
            sid: Socket ID of Pi client
            connected: Connection status
        """
        self.pi_sid = sid if connected else None
        self.pi_connected = connected
        status = "connected" if connected else "disconnected"
        logger.info(f"Pi {status}: {sid}")
    
    async def send_movement(self, movement_cmd: Dict) -> bool:
        """
        Send movement command to Pi.
        
        Args:
            movement_cmd: Dictionary with 'direction' and 'duration'
            
        Returns:
            Success status
        """
        if not self.pi_connected:
            logger.warning("Cannot send movement: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'movement_command',
                movement_cmd,
                room=self.pi_sid,
                namespace='/pi'
            )
            logger.info(f"Sent movement: {movement_cmd}")
            return True
        except Exception as e:
            logger.error(f"Error sending movement: {e}")
            return False
    
    async def send_stop(self) -> bool:
        """
        Send emergency stop command.
        
        Returns:
            Success status
        """
        if not self.pi_connected:
            logger.warning("Cannot send stop: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'stop_command',
                {},
                room=self.pi_sid,
                namespace='/pi'
            )
            logger.info("Sent stop command")
            return True
        except Exception as e:
            logger.error(f"Error sending stop: {e}")
            return False
    
    async def send_face_animation(self, keyframes: list, duration: float) -> bool:
        """
        Send face animation to Pi display.
        
        Args:
            keyframes: Animation keyframes
            duration: Total animation duration
            
        Returns:
            Success status
        """
        if not self.pi_connected:
            logger.warning("Cannot send animation: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'face_animation',
                {'keyframes': keyframes, 'duration': duration},
                room=self.pi_sid,
                namespace='/pi'
            )
            logger.info(f"Sent animation ({len(keyframes)} keyframes)")
            return True
        except Exception as e:
            logger.error(f"Error sending animation: {e}")
            return False
    
    async def send_audio(self, audio_path: str) -> bool:
        """
        Send audio file to Pi for playback.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Success status
        """
        if not self.pi_connected:
            logger.warning("Cannot send audio: Pi not connected")
            return False
        
        try:
            # Read and encode audio
            with open(audio_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode('utf-8')
            
            self.socketio.emit(
                'play_audio',
                {'audio_data': audio_data},
                room=self.pi_sid,
                namespace='/pi'
            )
            logger.info(f"Sent audio: {audio_path}")
            return True
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            return False
    
    async def execute_voice_command(self, text: str, ai_brain, tts_engine, 
                                     face_animator) -> bool:
        """
        Execute complete voice command pipeline.
        
        Args:
            text: Recognized speech text
            ai_brain: AI brain instance
            tts_engine: TTS engine instance
            face_animator: Face animator instance
            
        Returns:
            Success status
        """
        try:
            # Process with AI
            response_text, movement_cmd = ai_brain.process(text)
            
            # Generate TTS
            audio_path, phonemes = tts_engine.synthesize(response_text)
            
            # Generate face animation
            duration = phonemes[-1]['offset'] + phonemes[-1]['duration'] if phonemes else 2.0
            keyframes = face_animator.generate_lipsync(phonemes, duration)
            
            # Send to Pi
            if movement_cmd:
                await self.send_movement(movement_cmd)
            
            await self.send_face_animation(keyframes, duration)
            await self.send_audio(audio_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error executing voice command: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get robot status."""
        return {
            'pi_connected': self.pi_connected,
            'pi_sid': self.pi_sid
        }


if __name__ == "__main__":
    # Test robot controller
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("\n" + "="*60)
    print("ROBOT CONTROLLER TEST")
    print("="*60 + "\n")
    
    # Note: Full test requires SocketIO server running
    print("Robot controller requires SocketIO server for full testing.")
    print("See main.py for integration example.")
