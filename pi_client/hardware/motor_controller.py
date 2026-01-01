"""Motor controller with safety features for DC motors via GPIO."""

import RPi.GPIO as GPIO
import time
import signal
import sys
import atexit
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MotorController:
    """Control DC motors with emergency stop and safety features."""
    
    def __init__(self, config: dict):
        """Initialize motor controller with GPIO pins from config.
        
        Args:
            config: Configuration dict with motor pins and settings
        """
        self.config = config
        self.motor_pins = config['motor']['pins']
        self.running = False
        self.last_command_time = time.time()
        
        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        
        # Initialize all motor pins as output, set LOW
        for pin in self.motor_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("✓ Motor controller initialized (all motors OFF)")
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals for emergency stop."""
        logger.warning(f"Signal {signum} received - Emergency stop!")
        self.stop()
        self.cleanup()
        sys.exit(0)
    
    def move_forward(self, duration: Optional[float] = None):
        """Move forward.
        
        Args:
            duration: Time to move in seconds. None = continuous
        """
        logger.info(f"Moving forward" + (f" for {duration}s" if duration else ""))
        
        # Stop first for clean transition
        self.stop()
        time.sleep(0.05)
        
        # Left motor forward
        GPIO.output(self.motor_pins['L1'], GPIO.HIGH)
        GPIO.output(self.motor_pins['L2'], GPIO.LOW)
        
        # Right motor forward
        GPIO.output(self.motor_pins['R1'], GPIO.HIGH)
        GPIO.output(self.motor_pins['R2'], GPIO.LOW)
        
        self.running = True
        self.last_command_time = time.time()
        
        if duration:
            time.sleep(duration)
            self.stop()
    
    def move_backward(self, duration: Optional[float] = None):
        """Move backward.
        
        Args:
            duration: Time to move in seconds. None = continuous
        """
        logger.info(f"Moving backward" + (f" for {duration}s" if duration else ""))
        
        self.stop()
        time.sleep(0.05)
        
        # Left motor backward
        GPIO.output(self.motor_pins['L1'], GPIO.LOW)
        GPIO.output(self.motor_pins['L2'], GPIO.HIGH)
        
        # Right motor backward
        GPIO.output(self.motor_pins['R1'], GPIO.LOW)
        GPIO.output(self.motor_pins['R2'], GPIO.HIGH)
        
        self.running = True
        self.last_command_time = time.time()
        
        if duration:
            time.sleep(duration)
            self.stop()
    
    def turn_left(self, duration: float = 0.5):
        """Turn left by rotating in place.
        
        Args:
            duration: Time to turn in seconds
        """
        logger.info(f"Turning left for {duration}s")
        
        self.stop()
        time.sleep(0.05)
        
        # Left motor backward, right motor forward
        GPIO.output(self.motor_pins['L1'], GPIO.LOW)
        GPIO.output(self.motor_pins['L2'], GPIO.HIGH)
        GPIO.output(self.motor_pins['R1'], GPIO.HIGH)
        GPIO.output(self.motor_pins['R2'], GPIO.LOW)
        
        self.running = True
        self.last_command_time = time.time()
        
        time.sleep(duration)
        self.stop()
    
    def turn_right(self, duration: float = 0.5):
        """Turn right by rotating in place.
        
        Args:
            duration: Time to turn in seconds
        """
        logger.info(f"Turning right for {duration}s")
        
        self.stop()
        time.sleep(0.05)
        
        # Left motor forward, right motor backward
        GPIO.output(self.motor_pins['L1'], GPIO.HIGH)
        GPIO.output(self.motor_pins['L2'], GPIO.LOW)
        GPIO.output(self.motor_pins['R1'], GPIO.LOW)
        GPIO.output(self.motor_pins['R2'], GPIO.HIGH)
        
        self.running = True
        self.last_command_time = time.time()
        
        time.sleep(duration)
        self.stop()
    
    def stop(self):
        """Emergency stop - turn off all motors immediately."""
        for pin in self.motor_pins.values():
            GPIO.output(pin, GPIO.LOW)
        
        self.running = False
        logger.info("✓ Motors stopped")
    
    def cleanup(self):
        """Clean up GPIO on exit - CRITICAL for preventing stuck motors."""
        logger.info("Cleaning up GPIO pins...")
        self.stop()
        time.sleep(0.1)  # Ensure stop command completes
        
        try:
            GPIO.cleanup()
            logger.info("✓ GPIO cleanup complete")
        except Exception as e:
            logger.error(f"GPIO cleanup error: {e}")
    
    def check_timeout(self, max_timeout: float = 10.0):
        """Check if motors have been running too long without new command.
        
        Args:
            max_timeout: Maximum seconds without command before auto-stop
        
        Returns:
            bool: True if timeout triggered and motors stopped
        """
        if self.running and (time.time() - self.last_command_time) > max_timeout:
            logger.warning(f"Motor timeout ({max_timeout}s) - auto stopping")
            self.stop()
            return True
        return False
    
    def get_status(self) -> dict:
        """Get current motor status.
        
        Returns:
            dict: Status information
        """
        return {
            'running': self.running,
            'last_command': time.time() - self.last_command_time,
            'pins_state': {
                name: GPIO.input(pin)
                for name, pin in self.motor_pins.items()
            }
        }
