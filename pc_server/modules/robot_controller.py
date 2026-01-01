#!/usr/bin/env python3
"""
Robot Controller Module
Centralized robot command dispatcher and coordinator
"""

import logging
import asyncio
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)

class RobotController:
    """Centralized robot command dispatcher."""
    
    def __init__(self, config: Dict, socketio):
        """Initialize robot controller.
        
        Args:
            config: Configuration dictionary
            socketio: Flask-SocketIO instance for communication
        """
        self.config = config
        self.socketio = socketio
        self.pi_connected = False
        self.last_command_time = 0
        self.current_movement = None
        
        logger.info("Robot controller initialized")
    
    def set_pi_connected(self, connected: bool):
        """Update Pi connection status.
        
        Args:
            connected: Connection status
        """
        self.pi_connected = connected
        status = "connected" if connected else "disconnected"
        logger.info(f"Raspberry Pi {status}")
    
    async def send_movement(self, command: Dict) -> bool:
        """Send movement command to Pi.
        
        Args:
            command: Movement command dict with 'direction' and 'duration'
        
        Returns:
            True if command sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send movement: Pi not connected")
            return False
        
        try:
            self.current_movement = command
            self.last_command_time = time.time()
            
            # Send to Pi via SocketIO
            self.socketio.emit(
                'movement_command',
                command,
                namespace='/pi',
                room='pi_client'
            )
            
            logger.info(f"Sent movement: {command['direction']} for {command['duration']}s")
            return True
            
        except Exception as e:
            logger.error(f"Error sending movement: {e}")
            return False
    
    async def send_stop(self) -> bool:
        """Send emergency stop command.
        
        Returns:
            True if command sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send stop: Pi not connected")
            return False
        
        try:
            # Send stop command
            self.socketio.emit(
                'stop_command',
                {},
                namespace='/pi',
                room='pi_client'
            )
            
            self.current_movement = None
            logger.info("Sent STOP command")
            return True
            
        except Exception as e:
            logger.error(f"Error sending stop: {e}")
            return False
    
    async def send_face_animation(self, animation: Dict) -> bool:
        """Send face animation to Pi display.
        
        Args:
            animation: Animation data dict
        
        Returns:
            True if sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send animation: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'face_animation',
                animation,
                namespace='/pi',
                room='pi_display'
            )
            
            logger.info(f"Sent face animation: {animation['duration']:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error sending animation: {e}")
            return False
    
    async def send_audio(self, audio_path: str) -> bool:
        """Send audio file path to Pi for playback.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            True if sent successfully
        """
        if not self.pi_connected:
            logger.warning("Cannot send audio: Pi not connected")
            return False
        
        try:
            self.socketio.emit(
                'play_audio',
                {'audio_path': audio_path},
                namespace='/pi',
                room='pi_client'
            )
            
            logger.info(f"Sent audio: {audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current robot status.
        
        Returns:
            Status dictionary
        """
        return {
            'pi_connected': self.pi_connected,
            'current_movement': self.current_movement,
            'last_command_time': self.last_command_time,
            'uptime': time.time()
        }
    
    async def execute_command_sequence(self, commands: list) -> bool:
        """Execute a sequence of commands.
        
        Args:
            commands: List of command dictionaries
        
        Returns:
            True if all commands executed successfully
        """
        for cmd in commands:
            if cmd.get('type') == 'movement':
                success = await self.send_movement(cmd)
                if not success:
                    return False
                # Wait for movement duration
                await asyncio.sleep(cmd.get('duration', 0))
            
            elif cmd.get('type') == 'wait':
                await asyncio.sleep(cmd.get('duration', 0))
            
            elif cmd.get('type') == 'stop':
                await self.send_stop()
        
        return True


if __name__ == "__main__":
    # Test robot controller (mock)
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    # Mock socketio
    class MockSocketIO:
        def emit(self, event, data, **kwargs):
            print(f"EMIT: {event} -> {data}")
    
    controller = RobotController(config, MockSocketIO())
    controller.set_pi_connected(True)
    
    # Test commands
    async def test():
        print("\nTest 1: Single movement")
        await controller.send_movement({'direction': 'forward', 'duration': 3})
        
        print("\nTest 2: Stop command")
        await controller.send_stop()
        
        print("\nTest 3: Command sequence")
        sequence = [
            {'type': 'movement', 'direction': 'forward', 'duration': 2},
            {'type': 'wait', 'duration': 1},
            {'type': 'movement', 'direction': 'right', 'duration': 1.5},
            {'type': 'stop'}
        ]
        await controller.execute_command_sequence(sequence)
        
        print("\nTest 4: Status")
        status = controller.get_status()
        print(f"Status: {status}")
    
    asyncio.run(test())
