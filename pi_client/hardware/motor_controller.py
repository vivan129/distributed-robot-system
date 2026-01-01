#!/usr/bin/env python3
"""
Motor Controller Module - DC Motor Control with Safety

Handles 4-wheel DC motor control with multiple safety mechanisms:
- Emergency stop handlers
- GPIO cleanup on exit
- Movement timeout protection
- Signal handlers for graceful shutdown
"""

import logging
import RPi.GPIO as GPIO
import time
import signal
import sys
import atexit
from typing import Optional
import threading

logger = logging.getLogger(__name__)


class MotorController:
    """DC motor controller with safety features."""
    
    def __init__(self, config: dict):
        """
        Initialize motor controller.
        
        Args:
            config: Configuration dictionary with motor settings
        """
        motor_config = config.get('motors', {})
        self.pins = motor_config.get('pins', {})
        self.pin_mode = motor_config.get('pin_mode', 'BOARD')
        self.timeout = motor_config.get('timeout', 10)
        
        # Set GPIO mode
        if self.pin_mode == 'BOARD':
            GPIO.setmode(GPIO.BOARD)
        else:
            GPIO.setmode(GPIO.BCM)
        
        # Disable warnings
        GPIO.setwarnings(False)
        
        # Setup motor pins
        self.L1 = self.pins.get('L1', 33)
        self.L2 = self.pins.get('L2', 38)
        self.R1 = self.pins.get('R1', 35)
        self.R2 = self.pins.get('R2', 40)
        
        all_pins = [self.L1, self.L2, self.R1, self.R2]
        
        for pin in all_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Movement state
        self.is_moving = False
        self.current_direction = None
        self.stop_timer = None
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Motor controller initialized (pins: L1={self.L1}, L2={self.L2}, R1={self.R1}, R2={self.R2})")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {sig}, stopping motors...")
        self.stop()
        self.cleanup()
        sys.exit(0)
    
    def move(self, direction: str, duration: float = 0):
        """
        Move robot in specified direction.
        
        Args:
            direction: 'forward', 'backward', 'left', 'right', or 'stop'
            duration: Movement duration in seconds (0 = indefinite)
        """
        try:
            # Cancel existing timer
            if self.stop_timer:
                self.stop_timer.cancel()
            
            # Stop previous movement
            if self.is_moving:
                self._stop_motors()
            
            # Execute movement
            if direction == 'forward':
                self._move_forward()
            elif direction == 'backward':
                self._move_backward()
            elif direction == 'left':
                self._turn_left()
            elif direction == 'right':
                self._turn_right()
            elif direction == 'stop':
                self.stop()
                return
            else:
                logger.warning(f"Unknown direction: {direction}")
                return
            
            self.is_moving = True
            self.current_direction = direction
            logger.info(f"Moving {direction}" + (f" for {duration}s" if duration > 0 else ""))
            
            # Set timeout
            if duration > 0:
                self.stop_timer = threading.Timer(duration, self.stop)
                self.stop_timer.start()
        
        except Exception as e:
            logger.error(f"Movement error: {e}")
            self.stop()
    
    def _move_forward(self):
        """Move forward."""
        GPIO.output(self.L1, GPIO.HIGH)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.HIGH)
        GPIO.output(self.R2, GPIO.LOW)
    
    def _move_backward(self):
        """Move backward."""
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.HIGH)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.HIGH)
    
    def _turn_left(self):
        """Turn left."""
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.HIGH)
        GPIO.output(self.R1, GPIO.HIGH)
        GPIO.output(self.R2, GPIO.LOW)
    
    def _turn_right(self):
        """Turn right."""
        GPIO.output(self.L1, GPIO.HIGH)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.HIGH)
    
    def _stop_motors(self):
        """Stop all motors (internal)."""
        GPIO.output(self.L1, GPIO.LOW)
        GPIO.output(self.L2, GPIO.LOW)
        GPIO.output(self.R1, GPIO.LOW)
        GPIO.output(self.R2, GPIO.LOW)
    
    def stop(self):
        """Stop all motors (public)."""
        try:
            if self.stop_timer:
                self.stop_timer.cancel()
                self.stop_timer = None
            
            self._stop_motors()
            self.is_moving = False
            self.current_direction = None
            logger.info("Motors stopped")
        
        except Exception as e:
            logger.error(f"Stop error: {e}")
    
    def cleanup(self):
        """Cleanup GPIO pins."""
        try:
            logger.info("Cleaning up GPIO...")
            self.stop()
            GPIO.cleanup()
            logger.info("GPIO cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> dict:
        """Get motor status."""
        return {
            'is_moving': self.is_moving,
            'direction': self.current_direction
        }


if __name__ == "__main__":
    # Test motor controller
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize motors
    motors = MotorController(config)
    
    print("\n" + "="*60)
    print("MOTOR CONTROLLER TEST")
    print("="*60 + "\n")
    
    try:
        print("Testing forward...")
        motors.move('forward', 2)
        time.sleep(2.5)
        
        print("Testing backward...")
        motors.move('backward', 2)
        time.sleep(2.5)
        
        print("Testing left turn...")
        motors.move('left', 1)
        time.sleep(1.5)
        
        print("Testing right turn...")
        motors.move('right', 1)
        time.sleep(1.5)
        
        print("\nTest complete!")
    
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    finally:
        motors.cleanup()
