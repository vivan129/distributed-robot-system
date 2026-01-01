#!/usr/bin/env python3
"""
Ultrasonic Sensor Module - HC-SR04 Distance Measurement

Measures distance using HC-SR04 ultrasonic sensor for obstacle detection.
"""

import logging
import RPi.GPIO as GPIO
import time
from typing import Optional

logger = logging.getLogger(__name__)


class UltrasonicSensor:
    """HC-SR04 ultrasonic distance sensor."""
    
    def __init__(self, config: dict):
        """
        Initialize ultrasonic sensor.
        
        Args:
            config: Configuration dictionary with ultrasonic settings
        """
        ultrasonic_config = config.get('ultrasonic', {})
        self.trigger_pin = ultrasonic_config.get('trigger_pin', 11)
        self.echo_pin = ultrasonic_config.get('echo_pin', 13)
        self.max_distance = ultrasonic_config.get('max_distance', 400)
        self.timeout = ultrasonic_config.get('timeout', 0.05)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Initial state
        GPIO.output(self.trigger_pin, GPIO.LOW)
        time.sleep(0.1)
        
        logger.info(f"Ultrasonic sensor initialized (trigger={self.trigger_pin}, echo={self.echo_pin})")
    
    def measure_distance(self) -> Optional[float]:
        """
        Measure distance in centimeters.
        
        Returns:
            Distance in cm or None if measurement failed
        """
        try:
            # Send trigger pulse
            GPIO.output(self.trigger_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, GPIO.LOW)
            
            # Wait for echo
            pulse_start = time.time()
            timeout_start = pulse_start
            
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.time()
                if pulse_start - timeout_start > self.timeout:
                    logger.warning("Echo timeout (start)")
                    return None
            
            pulse_end = time.time()
            timeout_end = pulse_end
            
            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                if pulse_end - timeout_end > self.timeout:
                    logger.warning("Echo timeout (end)")
                    return None
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150  # Speed of sound / 2
            distance = round(distance, 2)
            
            # Validate reading
            if 2 <= distance <= self.max_distance:
                return distance
            else:
                return None
        
        except Exception as e:
            logger.error(f"Distance measurement error: {e}")
            return None
    
    def get_average_distance(self, samples: int = 3) -> Optional[float]:
        """
        Get average distance from multiple samples.
        
        Args:
            samples: Number of samples to average
            
        Returns:
            Average distance in cm or None
        """
        measurements = []
        
        for _ in range(samples):
            distance = self.measure_distance()
            if distance is not None:
                measurements.append(distance)
            time.sleep(0.06)  # 60ms between measurements
        
        if measurements:
            return sum(measurements) / len(measurements)
        return None
    
    def is_obstacle_detected(self, threshold: float = 30) -> bool:
        """
        Check if obstacle is within threshold distance.
        
        Args:
            threshold: Distance threshold in cm
            
        Returns:
            True if obstacle detected
        """
        distance = self.get_average_distance()
        if distance is not None:
            return distance < threshold
        return False


if __name__ == "__main__":
    # Test ultrasonic sensor
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize sensor
    sensor = UltrasonicSensor(config)
    
    print("\n" + "="*60)
    print("ULTRASONIC SENSOR TEST")
    print("="*60 + "\n")
    
    try:
        print("Taking distance measurements...\n")
        
        for i in range(10):
            distance = sensor.measure_distance()
            if distance:
                print(f"Measurement {i+1}: {distance:.2f} cm")
            else:
                print(f"Measurement {i+1}: Failed")
            time.sleep(0.5)
        
        print("\nTest complete!")
    
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    finally:
        GPIO.cleanup()
