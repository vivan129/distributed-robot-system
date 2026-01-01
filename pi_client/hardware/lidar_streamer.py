#!/usr/bin/env python3
"""
LiDAR Streamer Module
Handles RP-LIDAR A1 data capture and streaming
"""

import logging
import asyncio
from typing import Dict, AsyncGenerator, Optional
import time

try:
    from rplidar import RPLidar
    RPLIDAR_AVAILABLE = True
except ImportError:
    RPLIDAR_AVAILABLE = False
    logging.warning("rplidar library not available")

logger = logging.getLogger(__name__)

class LiDARStreamer:
    """RP-LIDAR A1 data streaming."""
    
    def __init__(self, config: Dict):
        """Initialize LiDAR streamer.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.lidar_config = config.get('lidar', {})
        
        if not RPLIDAR_AVAILABLE:
            raise RuntimeError("rplidar library not installed. Install with: pip install rplidar-roboticia")
        
        self.port = self.lidar_config.get('port', '/dev/ttyUSB0')
        self.baudrate = self.lidar_config.get('baudrate', 115200)
        self.timeout = self.lidar_config.get('timeout', 1.0)
        
        self.lidar = None
        self.is_streaming = False
        self.scan_count = 0
        
        self._connect()
    
    def _connect(self):
        """Connect to LiDAR."""
        try:
            logger.info(f"Connecting to RP-LIDAR on {self.port}...")
            self.lidar = RPLidar(self.port, baudrate=self.baudrate, timeout=self.timeout)
            
            # Get device info
            info = self.lidar.get_info()
            health = self.lidar.get_health()
            
            logger.info(f"LiDAR connected:")
            logger.info(f"  Model: {info['model']}")
            logger.info(f"  Firmware: {info['firmware'][0]}.{info['firmware'][1]}")
            logger.info(f"  Hardware: {info['hardware']}")
            logger.info(f"  Health: {health[0]}")
            
        except Exception as e:
            logger.error(f"LiDAR connection error: {e}")
            raise
    
    async def stream(self) -> AsyncGenerator[Dict, None]:
        """Stream LiDAR scans asynchronously.
        
        Yields:
            Dictionary with scan data and metadata
        """
        if not self.lidar:
            logger.error("LiDAR not connected")
            return
        
        self.is_streaming = True
        logger.info("LiDAR streaming started")
        
        try:
            # Start motor and scanning
            scan_mode = self.lidar_config.get('scan_mode', 'Standard')
            
            for scan in self.lidar.iter_scans(scan_type=scan_mode):
                if not self.is_streaming:
                    break
                
                # Extract ranges and angles
                ranges = []
                angles = []
                qualities = []
                
                for quality, angle, distance in scan:
                    ranges.append(distance / 1000.0)  # Convert mm to meters
                    angles.append(angle)
                    qualities.append(quality)
                
                self.scan_count += 1
                
                # Yield scan data
                yield {
                    'ranges': ranges,
                    'angles': angles,
                    'qualities': qualities,
                    'timestamp': time.time(),
                    'scan_number': self.scan_count,
                    'point_count': len(ranges)
                }
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"LiDAR streaming error: {e}")
        finally:
            self.stop_streaming()
        
        logger.info("LiDAR streaming stopped")
    
    def stop_streaming(self):
        """Stop LiDAR streaming."""
        self.is_streaming = False
        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.stop_motor()
                logger.info("LiDAR motor stopped")
            except Exception as e:
                logger.warning(f"Error stopping LiDAR: {e}")
    
    def disconnect(self):
        """Disconnect from LiDAR."""
        try:
            logger.info("Disconnecting LiDAR...")
            self.stop_streaming()
            
            if self.lidar:
                self.lidar.disconnect()
            
            logger.info("LiDAR disconnected")
        except Exception as e:
            logger.error(f"LiDAR disconnect error: {e}")
    
    def get_status(self) -> Dict:
        """Get LiDAR status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_streaming': self.is_streaming,
            'port': self.port,
            'scan_count': self.scan_count,
            'connected': self.lidar is not None
        }
    
    def reset(self):
        """Reset LiDAR connection."""
        try:
            logger.info("Resetting LiDAR...")
            if self.lidar:
                self.lidar.reset()
                time.sleep(2)  # Wait for reset
            self._connect()
        except Exception as e:
            logger.error(f"LiDAR reset error: {e}")


if __name__ == "__main__":
    # Test LiDAR streamer
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    lidar = LiDARStreamer(config)
    
    async def test():
        print("\nCapturing 5 scans...")
        scan_num = 0
        
        async for scan_data in lidar.stream():
            scan_num += 1
            print(f"Scan {scan_num}: {scan_data['point_count']} points")
            
            if scan_num >= 5:
                lidar.stop_streaming()
                break
        
        print("\nTest complete!")
    
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        lidar.disconnect()
