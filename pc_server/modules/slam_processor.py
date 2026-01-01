#!/usr/bin/env python3
"""
SLAM Processor Module - Mapping and Localization

Implements grid-based SLAM for RP-LIDAR A1 data.
Provides real-time mapping and robot localization.
"""

import logging
import numpy as np
from typing import List, Tuple, Optional, Dict
import cv2
import os

logger = logging.getLogger(__name__)


class SLAMProcessor:
    """SLAM processor for mapping and localization."""
    
    def __init__(self, config: dict):
        """
        Initialize SLAM processor.
        
        Args:
            config: Configuration dictionary with SLAM settings
        """
        map_config = config.get('map', {})
        self.resolution = map_config.get('resolution', 0.05)  # meters per pixel
        self.map_width = map_config.get('width', 2000)
        self.map_height = map_config.get('height', 2000)
        self.origin_x = map_config.get('origin_x', 1000)
        self.origin_y = map_config.get('origin_y', 1000)
        
        # Initialize map (0=unknown, 127=free, 255=occupied)
        self.map = np.full((self.map_height, self.map_width), 0, dtype=np.uint8)
        
        # Robot pose (x, y, theta)
        self.robot_pose = np.array([0.0, 0.0, 0.0])
        
        # LiDAR config
        lidar_config = config.get('lidar', {})
        self.range_min = lidar_config.get('range_min', 0.15)
        self.range_max = lidar_config.get('range_max', 12.0)
        
        # Statistics
        self.scan_count = 0
        
        # Create output directory
        self.output_dir = 'output/maps'
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"SLAM initialized (map: {self.map_width}x{self.map_height}, res: {self.resolution}m)")
    
    def add_scan(self, ranges: List[float], angles: List[float]):
        """
        Add LiDAR scan to map.
        
        Args:
            ranges: List of range measurements (meters)
            angles: List of angles (degrees)
        """
        try:
            robot_x, robot_y, robot_theta = self.robot_pose
            
            for distance, angle in zip(ranges, angles):
                # Filter invalid readings
                if distance < self.range_min or distance > self.range_max:
                    continue
                
                # Convert to radians and add robot orientation
                angle_rad = np.radians(angle) + robot_theta
                
                # Calculate endpoint in world coordinates
                endpoint_x = robot_x + distance * np.cos(angle_rad)
                endpoint_y = robot_y + distance * np.sin(angle_rad)
                
                # Convert to map coordinates
                map_x = int(self.origin_x + endpoint_x / self.resolution)
                map_y = int(self.origin_y - endpoint_y / self.resolution)
                
                # Mark as occupied if within bounds
                if 0 <= map_x < self.map_width and 0 <= map_y < self.map_height:
                    self.map[map_y, map_x] = 255
                
                # Ray tracing for free space
                robot_map_x = int(self.origin_x + robot_x / self.resolution)
                robot_map_y = int(self.origin_y - robot_y / self.resolution)
                
                self._bresenham_line(robot_map_x, robot_map_y, map_x, map_y)
            
            self.scan_count += 1
            
            if self.scan_count % 100 == 0:
                logger.debug(f"Processed {self.scan_count} scans")
        
        except Exception as e:
            logger.error(f"Error adding scan: {e}")
    
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int):
        """Mark free space along ray using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            # Mark as free (but don't overwrite occupied)
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                if self.map[y, x] == 0:
                    self.map[y, x] = 127
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def update_pose(self, x: float, y: float, theta: float):
        """
        Update robot pose.
        
        Args:
            x: X position (meters)
            y: Y position (meters)
            theta: Orientation (radians)
        """
        self.robot_pose = np.array([x, y, theta])
    
    def get_current_map(self) -> np.ndarray:
        """Get current occupancy grid map."""
        return self.map.copy()
    
    def get_map_with_robot(self) -> np.ndarray:
        """Get map with robot position visualized."""
        # Convert to color image
        map_color = cv2.cvtColor(self.map, cv2.COLOR_GRAY2BGR)
        
        # Draw robot position
        robot_x = int(self.origin_x + self.robot_pose[0] / self.resolution)
        robot_y = int(self.origin_y - self.robot_pose[1] / self.resolution)
        
        # Draw robot as circle
        cv2.circle(map_color, (robot_x, robot_y), 10, (0, 0, 255), -1)
        
        # Draw orientation arrow
        arrow_length = 30
        end_x = int(robot_x + arrow_length * np.cos(self.robot_pose[2]))
        end_y = int(robot_y - arrow_length * np.sin(self.robot_pose[2]))
        cv2.arrowedLine(map_color, (robot_x, robot_y), (end_x, end_y), 
                       (0, 255, 0), 3, tipLength=0.3)
        
        return map_color
    
    def save_map(self, filename: str = None):
        """Save map to file."""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"map_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        cv2.imwrite(filepath, self.map)
        logger.info(f"Map saved to {filepath}")
        return filepath
    
    def reset_map(self):
        """Reset map to empty state."""
        self.map = np.full((self.map_height, self.map_width), 0, dtype=np.uint8)
        self.robot_pose = np.array([0.0, 0.0, 0.0])
        self.scan_count = 0
        logger.info("Map reset")


if __name__ == "__main__":
    # Test SLAM processor
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/slam_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize SLAM
    slam = SLAMProcessor(config)
    
    print("\n" + "="*60)
    print("SLAM PROCESSOR TEST")
    print("="*60 + "\n")
    
    # Simulate scan data (square room)
    print("Simulating square room scan...")
    angles = list(range(0, 360, 1))
    ranges = [2.0] * len(angles)  # 2m to all sides
    
    slam.add_scan(ranges, angles)
    
    # Save map
    filepath = slam.save_map("test_map.png")
    print(f"\nMap saved: {filepath}")
    print(f"Total scans processed: {slam.scan_count}")
