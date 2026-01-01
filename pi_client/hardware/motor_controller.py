#!/usr/bin/env python3
"""
Motor Controller Module - DC Motor Control with Safety

Handles 4 DC motors using GPIO with multiple safety mechanisms
including signal handlers, emergency stop, and guaranteed cleanup.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import RPi.GPIO as GPIO
import time
import signal
import sys
import atexit
from typing import Dict, Optional
import threading

logger = logging.getLogger(__name__)


class MotorController:
    """Safe DC motor controller for Raspberry Pi robot."""
    
    def __init__(self, config: Dict):
        """
        Initialize motor controller.
        
        Args:
            config: Motor configuration dictionary
        """
        self.config = config.get('motors', {})
        
        # GPIO pin configuration (BOARD numbering)
        pins = self.config.get('pins', {})
        self.L1 = pins.get('L1', 33)  # Left forward
        self.L2 = pins.get('L2', 38)  # Left backward
        self.R1 = pins.get('R1', 35)  # Right forward
        self.R2 = pins.get('R2', 40)  # Right backward
        
        # Motor state
        self.current_direction = None
        self.is_moving = False
        self.last_command_time = time.time()
        
        # Timeout settings
        self.motor_timeout = self.config.get('motor_timeout', 10)
        self.timeout_timer = None
        
        # Initialize GPIO
        self._setup_gpio()
        
        # Register cleanup handlers
        self._register_cleanup_handlers()
        
        logger.info(f"Motor Controller initialized (pins: L1={self.L1}, L2={self.L2}, R1={self.R1}, R2={self.R2})")
    
    def _setup_gpio(self):
        """Setup GPIO pins for motor control."""
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BOARD)
            GPIO.setwarnings(False)
            
            # Setup motor pins as outputs
            motor_pins = [self.L1, self.L2, self.R1, self.R2]
            for pin in motor_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
            
            logger.info("GPIO pins configured successfully")
            
        except Exception as e:
            logger.error(f"GPIO setup failed: {e}")
            raise
    
    def _register_cleanup_handlers(self):
        """Register multiple cleanup handlers for safety."""
        # Register atexit handler
        atexit.register(self.cleanup)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Cleanup handlers registered")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.warning(f"Received signal {signum}, stopping motors...")
        self.stop()
        self.cleanup()
        sys.exit(0)
    
    def move(self, direction: str, duration: float = 0, speed: int = 75):
        """
        Move robot in specified direction.
        
        Args:
            direction: forward, backward, left, right
            duration: Movement duration in seconds (0 for continuous)
            speed: Motor speed 0-100% (reserved for PWM)
        """
        logger.info(f"Moving {direction} (duration={duration}s, speed={speed}%)")
        
        # Stop any existing movement
        self.stop()
        
        # Execute movement
        if direction == 'forward':
            self._forward()
        elif direction == 'backward':
            self._backward()
        elif direction == 'left':
            self._turn_left()
        elif direction == 'right':
            self._turn_right()
        else:
            logger.error(f"Unknown direction: {direction}")
            return
        
        self.current_direction = direction
        self.is_moving = True
        self.last_command_time = time.time()
        
        # Handle duration
        if duration > 0:
            # Start timer to stop after duration
            if self.timeout_timer:
                self.timeout_timer.cancel()
            
            self.timeout_timer = threading.Timer(duration, self.stop)
            self.timeout_timer.start()
    
    def _forward(self):
        """Move forward."""
        GPIO.output(self.L1, GPIO.HIGH)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.HIGH)
        GPIO.output(self.R2, GPIO.LOW)
        logger.debug("Motors: Forward")
    
    def _backward(self):
        """Move backward."""
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.HIGH)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.HIGH)
        logger.debug("Motors: Backward")
    
    def _turn_left(self):
        """Turn left (left motors backward, right motors forward)."""
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.HIGH)
        GPIO.output(self.R1, GPIO.HIGH)
        GPIO.output(self.R2, GPIO.LOW)
        logger.debug("Motors: Turn Left")
    
    def _turn_right(self):
        """Turn right (left motors forward, right motors backward)."""
        GPIO.output(self.L1, GPIO.HIGH)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.HIGH)
        logger.debug("Motors: Turn Right")
    
    def stop(self):
        """Stop all motors immediately."""
        # Cancel any timeout timer
        if self.timeout_timer:
            self.timeout_timer.cancel()
            self.timeout_timer = None
        
        # Set all motor pins LOW
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.LOW)
        
        self.is_moving = False
        self.current_direction = None
        
        logger.info("Motors stopped")
    
    def emergency_stop(self):
        """Emergency stop with maximum priority."""
        logger.warning("EMERGENCY STOP ACTIVATED")
        self.stop()
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            logger.info("Cleaning up motor controller...")
            
            # Stop motors
            self.stop()
            
            # Small delay to ensure stop completes
            time.sleep(0.1)
            
            # Cleanup GPIO
            GPIO.cleanup()
            
            logger.info("Motor controller cleanup complete")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_state(self) -> Dict:
        """Get current motor state."""
        return {
            'moving': self.is_moving,
            'direction': self.current_direction,
            'last_command': time.time() - self.last_command_time
        }
    
    def test_motors(self):
        """Test all motor directions."""
        logger.info("Testing motors...")
        
        test_duration = 1.0
        directions = ['forward', 'backward', 'left', 'right']
        
        for direction in directions:
            logger.info(f"Testing {direction}...")
            self.move(direction, duration=test_duration)
            time.sleep(test_duration + 0.5)
        
        logger.info("Motor test complete")


if __name__ == "__main__":
    # Test motor controller
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    motors = MotorController(config)
    
    try:
        # Run motor test
        print("\nStarting motor test in 3 seconds...")
        print("Press Ctrl+C to stop\n")
        time.sleep(3)
        
        motors.test_motors()
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        motors.cleanup()
