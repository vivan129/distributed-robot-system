"""RP-LIDAR A1 streaming module."""

import logging
import time
from typing import Generator, Tuple, List, Optional
import numpy as np

try:
    from rplidar import RPLidar
    RPLIDAR_AVAILABLE = True
except ImportError:
    RPLIDAR_AVAILABLE = False
    logging.warning("rplidar library not installed. Install with: pip install rplidar-roboticia")

logger = logging.getLogger(__name__)


class LidarStreamer:
    """Stream RP-LIDAR A1 scan data."""
    
    def __init__(self, config: dict):
        """Initialize LiDAR connection.
        
        Args:
            config: Configuration dict with LiDAR settings
        """
        if not RPLIDAR_AVAILABLE:
            raise ImportError("rplidar library not available")
        
        self.config = config
        self.lidar_config = config['lidar']
        self.lidar = None
        self.running = False
        
        if self.lidar_config.get('enabled', True):
            self._connect()
    
    def _connect(self):
        """Connect to LiDAR device."""
        try:
            port = self.lidar_config['port']
            baudrate = self.lidar_config.get('baudrate', 115200)
            
            logger.info(f"Connecting to LiDAR on {port}...")
            self.lidar = RPLidar(port, baudrate=baudrate)
            
            # Get device info
            info = self.lidar.get_info()
            health = self.lidar.get_health()
            
            logger.info(f"✓ RP-LIDAR A1 connected")
            logger.info(f"  Model: {info['model']}")
            logger.info(f"  Firmware: {info['firmware'][0]}.{info['firmware'][1]}")
            logger.info(f"  Hardware: {info['hardware']}")
            logger.info(f"  Health: {health[0]}")
            
        except Exception as e:
            logger.error(f"LiDAR connection failed: {e}")
            logger.error("Check:")
            logger.error("  1. Device connected to USB port")
            logger.error("  2. User in dialout group: sudo usermod -a -G dialout $USER")
            logger.error("  3. Port permissions: sudo chmod 666 /dev/ttyUSB0")
            raise
    
    def start_scan(self) -> Generator[Tuple[float, float, float], None, None]:
        """Start scanning and yield measurements.
        
        Yields:
            Tuple[float, float, float]: (quality, angle, distance)
                - quality: Measurement quality (0-255)
                - angle: Angle in degrees (0-360)
                - distance: Distance in millimeters
        """
        if not self.lidar:
            raise RuntimeError("LiDAR not connected")
        
        self.running = True
        logger.info("Starting LiDAR scan...")
        
        try:
            for scan in self.lidar.iter_scans():
                if not self.running:
                    break
                
                for measurement in scan:
                    quality, angle, distance = measurement
                    
                    # Filter based on config
                    min_dist = self.lidar_config.get('min_distance', 0.15) * 1000  # m to mm
                    max_dist = self.lidar_config.get('max_distance', 12.0) * 1000
                    
                    if min_dist <= distance <= max_dist:
                        yield (quality, angle, distance)
        
        except KeyboardInterrupt:
            logger.info("LiDAR scan interrupted")
        except Exception as e:
            logger.error(f"LiDAR scan error: {e}")
        finally:
            self.stop()
    
    def get_single_scan(self) -> Optional[List[Tuple[float, float, float]]]:
        """Get a single complete 360-degree scan.
        
        Returns:
            List of (quality, angle, distance) tuples, or None if failed
        """
        if not self.lidar:
            return None
        
        try:
            scan_data = []
            for scan in self.lidar.iter_scans():
                for measurement in scan:
                    scan_data.append(measurement)
                break  # Only get one complete rotation
            
            return scan_data
        
        except Exception as e:
            logger.error(f"Single scan failed: {e}")
            return None
    
    def get_scan_as_numpy(self) -> Optional[np.ndarray]:
        """Get scan as numpy array for processing.
        
        Returns:
            np.ndarray: Array of shape (N, 3) with columns [quality, angle, distance]
        """
        scan = self.get_single_scan()
        if scan:
            return np.array(scan)
        return None
    
    def get_scan_polar(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get scan in polar coordinates for visualization.
        
        Returns:
            Tuple of (angles, distances) as numpy arrays, or None if failed
        """
        scan = self.get_single_scan()
        if scan:
            angles = np.array([m[1] for m in scan])
            distances = np.array([m[2] for m in scan])
            return angles, distances
        return None
    
    def get_scan_cartesian(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Get scan in Cartesian coordinates.
        
        Returns:
            Tuple of (x, y) coordinates in meters, or None if failed
        """
        scan = self.get_single_scan()
        if scan:
            angles = np.radians([m[1] for m in scan])
            distances = np.array([m[2] / 1000.0 for m in scan])  # mm to meters
            
            x = distances * np.cos(angles)
            y = distances * np.sin(angles)
            
            return x, y
        return None
    
    def stop(self):
        """Stop LiDAR scanning."""
        self.running = False
        logger.info("LiDAR scan stopped")
    
    def cleanup(self):
        """Clean up LiDAR connection."""
        logger.info("Stopping LiDAR...")
        self.stop()
        
        try:
            if self.lidar:
                self.lidar.stop()
                self.lidar.stop_motor()
                self.lidar.disconnect()
            
            logger.info("✓ LiDAR disconnected")
        except Exception as e:
            logger.error(f"LiDAR cleanup error: {e}")
    
    def reset(self):
        """Reset LiDAR device."""
        logger.info("Resetting LiDAR...")
        try:
            if self.lidar:
                self.lidar.reset()
                time.sleep(2)
                logger.info("✓ LiDAR reset complete")
        except Exception as e:
            logger.error(f"LiDAR reset failed: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup()
