#!/usr/bin/env python3
"""
Ultrasonic Sensor Module
Handles HC-SR04 distance measurement
"""

import logging
import time
from typing import Dict, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for testing
    class MockGPIO:
        BOARD = 'BOARD'
        BCM = 'BCM'
        OUT = 'OUT'
        IN = 'IN'
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setwarnings(flag): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def input(pin): return 0
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()
    logging.warning("RPi.GPIO not available, using mock GPIO")

logger = logging.getLogger(__name__)

class UltrasonicSensor:
    """HC-SR04 ultrasonic distance sensor."""
    
    def __init__(self, config: Dict):
        """Initialize ultrasonic sensor.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.us_config = config.get('ultrasonic', {})
        
        # Setup GPIO
        pin_mode = config.get('motors', {}).get('pin_mode', 'BOARD')
        GPIO.setmode(GPIO.BOARD if pin_mode == 'BOARD' else GPIO.BCM)
        GPIO.setwarnings(False)
        
        self.trigger_pin = self.us_config.get('trigger_pin', 11)
        self.echo_pin = self.us_config.get('echo_pin', 13)
        self.max_distance = self.us_config.get('max_distance', 400)  # cm
        self.timeout = self.us_config.get('measurement_timeout', 0.5)
        self.samples = self.us_config.get('samples', 3)
        
        # Setup pins
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trigger_pin, GPIO.LOW)
        
        time.sleep(0.1)  # Settle time
        
        logger.info(f"Ultrasonic sensor initialized (Trigger: {self.trigger_pin}, Echo: {self.echo_pin})")
    
    def measure_once(self) -> Optional[float]:
        """Measure distance once.
        
        Returns:
            Distance in cm or None if timeout
        """
        try:
            # Send trigger pulse
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, GPIO.LOW)
            
            # Wait for echo start
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.time()
                if (pulse_start - timeout_start) > self.timeout:
                    return None
            
            # Wait for echo end
            timeout_start = time.time()
            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                if (pulse_end - timeout_start) > self.timeout:
                    return None
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150  # Speed of sound / 2
            distance = round(distance, 2)
            
            # Validate range
            if 2 <= distance <= self.max_distance:
                return distance
            else:
                return None
                
        except Exception as e:
            logger.error(f"Measurement error: {e}")
            return None
    
    def measure(self) -> Optional[float]:
        """Measure distance with averaging.
        
        Returns:
            Average distance in cm or None if failed
        """
        measurements = []
        
        for _ in range(self.samples):
            distance = self.measure_once()
            if distance is not None:
                measurements.append(distance)
            time.sleep(0.05)  # 50ms between samples
        
        if measurements:
            avg_distance = sum(measurements) / len(measurements)
            logger.debug(f"Distance: {avg_distance:.2f} cm")
            return round(avg_distance, 2)
        else:
            logger.warning("All measurements failed")
            return None
    
    def is_obstacle_close(self, threshold: float = None) -> bool:
        """Check if obstacle is within threshold.
        
        Args:
            threshold: Distance threshold in cm (uses config if None)
        
        Returns:
            True if obstacle detected within threshold
        """
        if threshold is None:
            threshold = self.config.get('safety', {}).get('obstacle_threshold', 30)
        
        distance = self.measure()
        if distance is not None and distance < threshold:
            logger.warning(f"Obstacle detected at {distance:.2f} cm!")
            return True
        return False
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            logger.info("Cleaning up ultrasonic sensor GPIO...")
            # Note: Don't call GPIO.cleanup() here as motors also use GPIO
            # Cleanup should be done once in main program
            logger.info("Ultrasonic sensor cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict:
        """Get sensor status.
        
        Returns:
            Status dictionary
        """
        return {
            'trigger_pin': self.trigger_pin,
            'echo_pin': self.echo_pin,
            'max_distance': self.max_distance,
            'samples': self.samples
        }


if __name__ == "__main__":
    # Test ultrasonic sensor
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    sensor = UltrasonicSensor(config)
    
    try:
        print("\nMeasuring distance 10 times (press Ctrl+C to stop)...")
        for i in range(10):
            distance = sensor.measure()
            if distance:
                print(f"{i+1}. Distance: {distance:.2f} cm")
            else:
                print(f"{i+1}. Measurement failed")
            time.sleep(1)
        
        print("\nTest obstacle detection (threshold=30cm)")
        if sensor.is_obstacle_close(30):
            print("⚠️  Obstacle detected!")
        else:
            print("✓ Path clear")
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        sensor.cleanup()
