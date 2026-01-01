"""HC-SR04 ultrasonic distance sensor module."""

import RPi.GPIO as GPIO
import time
import logging
from typing import Optional
import statistics

logger = logging.getLogger(__name__)


class UltrasonicSensor:
    """HC-SR04 ultrasonic distance sensor interface."""
    
    def __init__(self, config: dict):
        """Initialize ultrasonic sensor.
        
        Args:
            config: Configuration dict with ultrasonic settings
        """
        self.config = config
        self.ultrasonic_config = config['ultrasonic']
        
        if not self.ultrasonic_config.get('enabled', True):
            logger.info("Ultrasonic sensor disabled in config")
            return
        
        self.trigger_pin = self.ultrasonic_config['trigger_pin']
        self.echo_pin = self.ultrasonic_config['echo_pin']
        self.max_distance = self.ultrasonic_config.get('max_distance', 400)  # cm
        self.timeout = self.ultrasonic_config.get('measurement_timeout', 0.05)  # seconds
        
        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Ensure trigger is low
        GPIO.output(self.trigger_pin, GPIO.LOW)
        time.sleep(0.1)
        
        logger.info(f"✓ Ultrasonic sensor initialized (Trig: {self.trigger_pin}, Echo: {self.echo_pin})")
    
    def measure_distance(self) -> Optional[float]:
        """Measure distance to nearest object.
        
        Returns:
            float: Distance in centimeters, or None if measurement failed
        """
        try:
            # Send 10us pulse to trigger
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, GPIO.LOW)
            
            # Wait for echo start
            pulse_start = time.time()
            timeout_start = pulse_start
            
            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout_start > self.timeout:
                    logger.warning("Ultrasonic timeout waiting for echo start")
                    return None
            
            # Wait for echo end
            pulse_end = time.time()
            timeout_end = pulse_end
            
            while GPIO.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end - timeout_end > self.timeout:
                    logger.warning("Ultrasonic timeout waiting for echo end")
                    return None
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            
            # Speed of sound: 343 m/s = 34300 cm/s
            # Distance = (Time × Speed) / 2 (round trip)
            distance = (pulse_duration * 34300) / 2
            
            # Validate measurement
            if 2 <= distance <= self.max_distance:
                return round(distance, 2)
            else:
                logger.debug(f"Out of range measurement: {distance} cm")
                return None
        
        except Exception as e:
            logger.error(f"Distance measurement error: {e}")
            return None
    
    def get_average_distance(self, samples: int = 5) -> Optional[float]:
        """Get average distance from multiple measurements.
        
        Args:
            samples: Number of measurements to average
        
        Returns:
            float: Average distance in cm, or None if failed
        """
        measurements = []
        
        for _ in range(samples):
            distance = self.measure_distance()
            if distance is not None:
                measurements.append(distance)
            time.sleep(0.01)  # Small delay between measurements
        
        if not measurements:
            return None
        
        # Return median to filter outliers
        return round(statistics.median(measurements), 2)
    
    def get_filtered_distance(self, samples: int = 5, outlier_threshold: float = 10.0) -> Optional[float]:
        """Get distance with outlier filtering.
        
        Args:
            samples: Number of measurements to take
            outlier_threshold: Maximum allowed deviation from median (cm)
        
        Returns:
            float: Filtered average distance in cm, or None if failed
        """
        measurements = []
        
        for _ in range(samples):
            distance = self.measure_distance()
            if distance is not None:
                measurements.append(distance)
            time.sleep(0.01)
        
        if len(measurements) < 3:
            return None
        
        # Calculate median
        median = statistics.median(measurements)
        
        # Filter outliers
        filtered = [d for d in measurements if abs(d - median) <= outlier_threshold]
        
        if filtered:
            return round(sum(filtered) / len(filtered), 2)
        return None
    
    def is_obstacle_detected(self, threshold: Optional[float] = None) -> bool:
        """Check if obstacle is within threshold distance.
        
        Args:
            threshold: Distance threshold in cm. Uses config default if None.
        
        Returns:
            bool: True if obstacle detected within threshold
        """
        if threshold is None:
            threshold = self.config['safety']['obstacle_threshold']
        
        distance = self.get_average_distance(samples=3)
        
        if distance is None:
            return False
        
        return distance < threshold
    
    def get_status(self) -> dict:
        """Get sensor status and current reading.
        
        Returns:
            dict: Status information
        """
        distance = self.get_average_distance(samples=3)
        
        return {
            'enabled': self.ultrasonic_config.get('enabled', True),
            'distance_cm': distance,
            'trigger_pin': self.trigger_pin,
            'echo_pin': self.echo_pin,
            'max_distance': self.max_distance
        }
    
    def cleanup(self):
        """Clean up GPIO pins."""
        logger.info("Cleaning up ultrasonic sensor GPIO...")
        try:
            GPIO.output(self.trigger_pin, GPIO.LOW)
            logger.info("✓ Ultrasonic sensor cleanup complete")
        except Exception as e:
            logger.error(f"Ultrasonic cleanup error: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup()
