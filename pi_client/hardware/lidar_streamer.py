#!/usr/bin/env python3
"""
LiDAR Streamer Module - RP-LIDAR A1 Data Streaming

Streams LiDAR scan data to PC for SLAM processing.
Handles RP-LIDAR A1 connection and data collection.
"""

import logging
import asyncio
from typing import List, Tuple, Optional
from rplidar import RPLidar
import numpy as np

logger = logging.getLogger(__name__)


class LiDARStreamer:
    """RP-LIDAR A1 data streamer."""
    
    def __init__(self, config: dict):
        """
        Initialize LiDAR streamer.
        
        Args:
            config: Configuration dictionary with LiDAR settings
        """
        lidar_config = config.get('lidar', {})
        self.port = lidar_config.get('port', '/dev/ttyUSB0')
        self.baudrate = lidar_config.get('baudrate', 115200)
        self.max_distance = lidar_config.get('max_distance', 12.0)
        self.min_distance = lidar_config.get('min_distance', 0.15)
        
        self.lidar = None
        self.is_streaming = False
        
        self._initialize_lidar()
    
    def _initialize_lidar(self):
        """Initialize LiDAR connection."""
        try:
            self.lidar = RPLidar(self.port, baudrate=self.baudrate)
            
            # Get device info
            info = self.lidar.get_info()
            health = self.lidar.get_health()
            
            logger.info(f"LiDAR connected: {self.port}")
            logger.info(f"Model: {info['model']} S/N: {info['serialnumber']}")
            logger.info(f"Health: {health}")
        
        except Exception as e:
            logger.error(f"LiDAR initialization failed: {e}")
            raise
    
    def get_single_scan(self) -> Tuple[List[float], List[float]]:
        """
        Get single 360° scan.
        
        Returns:
            Tuple of (ranges, angles) in meters and degrees
        """
        try:
            ranges = []
            angles = []
            
            for scan in self.lidar.iter_scans():
                for (quality, angle, distance) in scan:
                    # Convert to meters
                    distance_m = distance / 1000.0
                    
                    # Filter by range
                    if self.min_distance <= distance_m <= self.max_distance:
                        ranges.append(distance_m)
                        angles.append(angle)
                
                # Return after one complete scan
                break
            
            return ranges, angles
        
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return [], []
    
    async def stream_scans(self, callback) -> None:
        """
        Stream scans asynchronously.
        
        Args:
            callback: Async function to call with scan data
        """
        self.is_streaming = True
        logger.info("Started LiDAR streaming")
        
        try:
            for scan in self.lidar.iter_scans():
                if not self.is_streaming:
                    break
                
                ranges = []
                angles = []
                
                for (quality, angle, distance) in scan:
                    distance_m = distance / 1000.0
                    
                    if self.min_distance <= distance_m <= self.max_distance:
                        ranges.append(distance_m)
                        angles.append(angle)
                
                # Send scan data
                await callback({'ranges': ranges, 'angles': angles})
                
                # Small delay for CPU
                await asyncio.sleep(0.01)
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        
        finally:
            logger.info("Stopped LiDAR streaming")
    
    def stop_streaming(self):
        """Stop streaming."""
        self.is_streaming = False
    
    def release(self):
        """Release LiDAR resources."""
        try:
            self.stop_streaming()
            
            if self.lidar:
                self.lidar.stop()
                self.lidar.disconnect()
            
            logger.info("LiDAR released")
        
        except Exception as e:
            logger.error(f"LiDAR release error: {e}")


if __name__ == "__main__":
    # Test LiDAR streamer
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize LiDAR
    lidar = LiDARStreamer(config)
    
    print("\n" + "="*60)
    print("LIDAR STREAMER TEST")
    print("="*60 + "\n")
    
    try:
        print("Capturing test scans...\n")
        
        for i in range(3):
            ranges, angles = lidar.get_single_scan()
            print(f"Scan {i+1}: {len(ranges)} points")
            if ranges:
                print(f"  Range: {min(ranges):.2f}m - {max(ranges):.2f}m")
        
        print("\nTest complete!")
    
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    finally:
        lidar.release()
