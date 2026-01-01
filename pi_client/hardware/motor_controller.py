"""
Motor Controller - DC motor control with safety mechanisms
Adapted from working code with multiple shutdown handlers
"""

import RPi.GPIO as GPIO
import time
import asyncio
import atexit
import signal
import sys
import logging

logger = logging.getLogger(__name__)


class MotorController:
    def __init__(self, config):
        self.MOTORS = config['motor_pins']
        
        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        
        for pin in self.MOTORS.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            GPIO.output(pin, GPIO.LOW)
            
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)
        
        logger.info("✓ Motors initialized (all OFF)")
        
    def _signal_handler(self, signum, frame):
        """Handle signals"""
        self.cleanup()
        sys.exit(0)
        
    def stop(self):
        """FORCE stop all motors immediately"""
        for pin in self.MOTORS.values():
            try:
                GPIO.output(pin, GPIO.LOW)
            except:
                pass
        time.sleep(0.01)
        logger.info("⚠️  Motors STOPPED")
        
    def move(self, direction):
        """
        Move in direction
        Always stops all motors first for safety
        """
        # Always stop first
        self.stop()
        
        direction = direction.lower()
        
        if direction in ["f", "forward"]:
            GPIO.output(self.MOTORS['L1'], GPIO.HIGH)
            GPIO.output(self.MOTORS['R1'], GPIO.HIGH)
            logger.info("↑ Moving forward")
        elif direction in ["b", "backward", "back"]:
            GPIO.output(self.MOTORS['L2'], GPIO.HIGH)
            GPIO.output(self.MOTORS['R2'], GPIO.HIGH)
            logger.info("↓ Moving backward")
        elif direction in ["l", "left"]:
            GPIO.output(self.MOTORS['L2'], GPIO.HIGH)
            GPIO.output(self.MOTORS['R1'], GPIO.HIGH)
            logger.info("← Turning left")
        elif direction in ["r", "right"]:
            GPIO.output(self.MOTORS['L1'], GPIO.HIGH)
            GPIO.output(self.MOTORS['R2'], GPIO.HIGH)
            logger.info("→ Turning right")
        elif direction == "stop":
            pass  # Already stopped
            
    async def move_timed(self, direction, seconds):
        """
        Move for specified duration then stop
        """
        self.move(direction)
        await asyncio.sleep(seconds)
        self.stop()
        logger.info(f"Timed movement complete: {direction} for {seconds}s")
        
    def cleanup(self):
        """Emergency cleanup - called on exit"""
        logger.info("🛑 EMERGENCY STOP ACTIVATED")
        
        # Stop motors multiple times to be absolutely sure
        for _ in range(3):
            for pin in self.MOTORS.values():
                try:
                    GPIO.output(pin, GPIO.LOW)
                except:
                    pass
            time.sleep(0.05)
            
        # GPIO cleanup
        try:
            GPIO.cleanup()
            logger.info("✓ GPIO cleaned up")
        except:
            pass
