#!/usr/bin/env python3
"""
LiDAR Module - Laser Scanner Wrapper
Wraps LidarStreamer with simpler interface for main.py
"""

import logging
from typing import Dict, Optional
from .lidar_streamer import LidarStreamer

logger = logging.getLogger(__name__)


class LidarModule:
    """Simplified LiDAR interface for main Pi client."""
    
    def __init__(self, config: dict):
        """
        Initialize LiDAR module.
        
        Args:
            config: Full robot configuration dictionary
        """
        self.streamer = LidarStreamer(config)
        self.config = config.get('lidar', {})
        logger.info("LiDAR module initialized")
    
    def get_scan(self) -> Optional[Dict]:
        """
        Get LiDAR scan data.
        
        Returns:
            Dictionary with 'ranges' (list of distances) and 'angles' (list of angles)
            or None on error
        """
        try:
            scan_data = self.streamer.get_scan()
            if scan_data:
                return {
                    'ranges': scan_data['ranges'],
                    'angles': scan_data['angles']
                }
            return None
        except Exception as e:
            logger.error(f"Error getting LiDAR scan: {e}")
            return None
    
    def get_full_scan(self):
        """Get full scan data with quality information."""
        return self.streamer.get_scan()
    
    def stop(self):
        """Stop LiDAR scanning."""
        self.streamer.stop()
        logger.info("LiDAR module stopped")


if __name__ == "__main__":
    import yaml
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    lidar = LidarModule(config)
    
    print("Testing LiDAR module...")
    time.sleep(1)  # Let it warm up
    
    scan = lidar.get_scan()
    if scan:
        print(f"Scan data: {len(scan['ranges'])} points")
        print(f"Min distance: {min(scan['ranges']):.2f}m")
        print(f"Max distance: {max(scan['ranges']):.2f}m")
    else:
        print("Failed to get scan")
    
    lidar.stop()
