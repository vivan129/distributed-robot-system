#!/usr/bin/env python3
"""
Motor Controller Module - DC Motor Control with Safety
Handles 4x DC motor control with emergency stop and cleanup
"""

import logging
import time
import signal
import sys
import atexit
from typing import Dict
try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for testing on non-Pi systems
    class MockGPIO:
        BOARD = 'BOARD'
        BCM = 'BCM'
        OUT = 'OUT'
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setwarnings(flag): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pins, state): pass
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()
    logging.warning("RPi.GPIO not available, using mock GPIO")

logger = logging.getLogger(__name__)

class MotorController:
    """DC motor controller with safety features."""
    
    def __init__(self, config: Dict):
        """Initialize motor controller.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.motor_config = config.get('motors', {})
        self.pins = self.motor_config.get('pins', {})
        
        # Setup GPIO
        pin_mode = self.motor_config.get('pin_mode', 'BOARD')
        GPIO.setmode(GPIO.BOARD if pin_mode == 'BOARD' else GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup motor pins
        self.L1 = self.pins.get('L1', 33)  # Left forward
        self.L2 = self.pins.get('L2', 38)  # Left backward
        self.R1 = self.pins.get('R1', 35)  # Right forward
        self.R2 = self.pins.get('R2', 40)  # Right backward
        
        all_pins = [self.L1, self.L2, self.R1, self.R2]
        GPIO.setup(all_pins, GPIO.OUT)
        
        # Initialize all motors OFF
        GPIO.output(all_pins, GPIO.LOW)
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.is_moving = False
        self.current_direction = None
        
        logger.info(f"Motor controller initialized (pins: L1={self.L1}, L2={self.L2}, R1={self.R1}, R2={self.R2})")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.warning(f"Signal {signum} received, stopping motors...")
        self.stop()
        self.cleanup()
        sys.exit(0)
    
    def forward(self, duration: float = 0):
        """Move forward.
        
        Args:
            duration: Time to move (0 = continuous)
        """
        logger.info(f"Moving FORWARD for {duration}s")
        GPIO.output([self.L1, self.R1], GPIO.HIGH)
        GPIO.output([self.L2, self.R2], GPIO.LOW)
        self.is_moving = True
        self.current_direction = 'forward'
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def backward(self, duration: float = 0):
        """Move backward.
        
        Args:
            duration: Time to move (0 = continuous)
        """
        logger.info(f"Moving BACKWARD for {duration}s")
        GPIO.output([self.L2, self.R2], GPIO.HIGH)
        GPIO.output([self.L1, self.R1], GPIO.LOW)
        self.is_moving = True
        self.current_direction = 'backward'
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def left(self, duration: float = 0):
        """Turn left (rotate in place).
        
        Args:
            duration: Time to turn (0 = continuous)
        """
        logger.info(f"Turning LEFT for {duration}s")
        GPIO.output([self.L2, self.R1], GPIO.HIGH)  # Left back, right forward
        GPIO.output([self.L1, self.R2], GPIO.LOW)
        self.is_moving = True
        self.current_direction = 'left'
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def right(self, duration: float = 0):
        """Turn right (rotate in place).
        
        Args:
            duration: Time to turn (0 = continuous)
        """
        logger.info(f"Turning RIGHT for {duration}s")
        GPIO.output([self.L1, self.R2], GPIO.HIGH)  # Left forward, right back
        GPIO.output([self.L2, self.R1], GPIO.LOW)
        self.is_moving = True
        self.current_direction = 'right'
        
        if duration > 0:
            time.sleep(duration)
            self.stop()
    
    def stop(self):
        """Stop all motors immediately."""
        logger.info("STOP - All motors OFF")
        GPIO.output([self.L1, self.L2, self.R1, self.R2], GPIO.LOW)
        self.is_moving = False
        self.current_direction = None
    
    def move(self, direction: str, duration: float = 2.0):
        """Move in specified direction.
        
        Args:
            direction: 'forward', 'backward', 'left', 'right', 'stop'
            duration: Time to move in seconds
        """
        direction = direction.lower()
        
        if direction == 'forward':
            self.forward(duration)
        elif direction == 'backward':
            self.backward(duration)
        elif direction == 'left':
            self.left(duration)
        elif direction == 'right':
            self.right(duration)
        elif direction == 'stop':
            self.stop()
        else:
            logger.warning(f"Unknown direction: {direction}")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            logger.info("Cleaning up GPIO...")
            self.stop()
            GPIO.cleanup()
            logger.info("GPIO cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get current motor status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_moving': self.is_moving,
            'direction': self.current_direction,
            'pins': {
                'L1': self.L1,
                'L2': self.L2,
                'R1': self.R1,
                'R2': self.R2
            }
        }


if __name__ == "__main__":
    # Test motor controller
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    motors = MotorController(config)
    
    try:
        print("\nTest sequence (each move 2 seconds)")
        print("1. Forward")
        motors.forward(2)
        time.sleep(0.5)
        
        print("2. Backward")
        motors.backward(2)
        time.sleep(0.5)
        
        print("3. Left")
        motors.left(1.5)
        time.sleep(0.5)
        
        print("4. Right")
        motors.right(1.5)
        time.sleep(0.5)
        
        print("5. Stop")
        motors.stop()
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        motors.cleanup()
