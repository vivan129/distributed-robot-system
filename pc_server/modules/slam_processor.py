#!/usr/bin/env python3
"""
SLAM Processor Module
Handles simultaneous localization and mapping from LiDAR data
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
import cv2
import os

logger = logging.getLogger(__name__)

class SLAMProcessor:
    """Grid-based SLAM processor for LiDAR data."""
    
    def __init__(self, config: Dict):
        """Initialize SLAM processor.
        
        Args:
            config: Configuration dictionary from slam_config.yaml
        """
        self.config = config
        self.map_config = config.get('map', {})
        
        # Initialize occupancy grid
        width = self.map_config.get('width', 2000)
        height = self.map_config.get('height', 2000)
        unknown = self.map_config.get('unknown_value', 128)
        
        self.grid = np.full((height, width), unknown, dtype=np.uint8)
        self.log_odds_grid = np.zeros((height, width), dtype=np.float32)
        
        # Robot pose (x, y, theta)
        origin = self.map_config.get('origin', [width // 2, height // 2])
        self.pose = np.array([origin[0], origin[1], 0.0], dtype=np.float32)
        
        # Resolution (meters per pixel)
        self.resolution = self.map_config.get('resolution', 0.05)
        
        # Log odds parameters
        grid_config = config.get('grid_mapping', {})
        self.log_odds_hit = grid_config.get('log_odds_hit', 0.85)
        self.log_odds_miss = grid_config.get('log_odds_miss', -0.4)
        self.max_log_odds = grid_config.get('max_log_odds', 3.5)
        self.min_log_odds = grid_config.get('min_log_odds', -3.5)
        
        # Thresholds
        self.free_threshold = self.map_config.get('free_threshold', 0.196)
        self.occupied_threshold = self.map_config.get('occupied_threshold', 0.65)
        
        logger.info(f"SLAM processor initialized: {width}x{height} @ {self.resolution}m/pixel")
    
    def add_scan(self, ranges: List[float], angles: List[float]):
        """Add a LiDAR scan to the map.
        
        Args:
            ranges: List of range measurements (meters)
            angles: List of corresponding angles (degrees)
        """
        try:
            # Convert to numpy arrays
            ranges = np.array(ranges)
            angles = np.deg2rad(angles)
            
            # Filter invalid ranges
            lidar_config = self.config.get('lidar', {})
            min_range = lidar_config.get('range_min', 0.15)
            max_range = lidar_config.get('range_max', 12.0)
            
            valid = (ranges >= min_range) & (ranges <= max_range)
            ranges = ranges[valid]
            angles = angles[valid]
            
            if len(ranges) == 0:
                return
            
            # Robot pose
            x_robot, y_robot, theta_robot = self.pose
            
            # Convert scan to world coordinates
            world_angles = angles + theta_robot
            x_points = x_robot + ranges / self.resolution * np.cos(world_angles)
            y_points = y_robot + ranges / self.resolution * np.sin(world_angles)
            
            # Update occupancy grid using ray tracing
            for x_end, y_end in zip(x_points, y_points):
                self._ray_trace_update(x_robot, y_robot, x_end, y_end)
            
            # Convert log odds to probability for visualization
            self._update_grid_from_log_odds()
            
        except Exception as e:
            logger.error(f"Error adding scan: {e}")
    
    def _ray_trace_update(self, x0: float, y0: float, x1: float, y1: float):
        """Update grid along a ray using Bresenham's algorithm.
        
        Args:
            x0, y0: Start point (robot position)
            x1, y1: End point (obstacle)
        """
        # Bresenham's line algorithm
        x0, y0 = int(x0), int(y0)
        x1, y1 = int(x1), int(y1)
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            # Check bounds
            if 0 <= y < self.grid.shape[0] and 0 <= x < self.grid.shape[1]:
                # Update cell (miss if not at end, hit if at end)
                if x == x1 and y == y1:
                    # Hit (obstacle)
                    self.log_odds_grid[y, x] += self.log_odds_hit
                else:
                    # Miss (free space)
                    self.log_odds_grid[y, x] += self.log_odds_miss
                
                # Clamp values
                self.log_odds_grid[y, x] = np.clip(
                    self.log_odds_grid[y, x],
                    self.min_log_odds,
                    self.max_log_odds
                )
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def _update_grid_from_log_odds(self):
        """Convert log odds to probability and update visualization grid."""
        # Convert log odds to probability
        prob = 1.0 - 1.0 / (1.0 + np.exp(self.log_odds_grid))
        
        # Threshold to occupancy values
        self.grid = np.full_like(self.grid, self.map_config.get('unknown_value', 128))
        self.grid[prob < self.free_threshold] = 255  # Free
        self.grid[prob > self.occupied_threshold] = 0  # Occupied
    
    def update_pose(self, x: float, y: float, theta: float):
        """Update robot pose.
        
        Args:
            x, y: Position in pixels
            theta: Orientation in radians
        """
        self.pose = np.array([x, y, theta], dtype=np.float32)
    
    def get_current_map(self) -> np.ndarray:
        """Get current occupancy grid map.
        
        Returns:
            Occupancy grid as numpy array (0=occupied, 255=free, 128=unknown)
        """
        return self.grid.copy()
    
    def get_map_with_robot(self) -> np.ndarray:
        """Get map with robot position marked.
        
        Returns:
            RGB map image with robot position
        """
        # Convert to RGB
        map_rgb = cv2.cvtColor(self.grid, cv2.COLOR_GRAY2RGB)
        
        # Draw robot position
        x, y, theta = self.pose.astype(int)
        if 0 <= x < map_rgb.shape[1] and 0 <= y < map_rgb.shape[0]:
            # Robot body (blue circle)
            cv2.circle(map_rgb, (x, y), 10, (255, 0, 0), -1)
            
            # Direction indicator (red line)
            dx = int(20 * np.cos(theta))
            dy = int(20 * np.sin(theta))
            cv2.line(map_rgb, (x, y), (x + dx, y + dy), (0, 0, 255), 2)
        
        return map_rgb
    
    def save_map(self, filename: str):
        """Save map to file.
        
        Args:
            filename: Output filename (.pgm or .png)
        """
        try:
            cv2.imwrite(filename, self.grid)
            logger.info(f"Map saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving map: {e}")
    
    def reset_map(self):
        """Reset map to unknown state."""
        unknown = self.map_config.get('unknown_value', 128)
        self.grid.fill(unknown)
        self.log_odds_grid.fill(0)
        logger.info("Map reset")


if __name__ == "__main__":
    # Test SLAM processor
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('config/slam_config.yaml') as f:
        config = yaml.safe_load(f)
    
    slam = SLAMProcessor(config)
    
    print("\nTest 1: Simulated scan")
    # Simulate a simple scan (square room)
    angles = np.linspace(0, 360, 360)
    ranges = np.full(360, 5.0)  # 5 meters all around
    
    slam.add_scan(ranges.tolist(), angles.tolist())
    
    # Save map
    os.makedirs('maps', exist_ok=True)
    slam.save_map('maps/test_map.png')
    print(f"Map saved: maps/test_map.png")
    
    # Get map with robot
    map_with_robot = slam.get_map_with_robot()
    cv2.imwrite('maps/test_map_robot.png', map_with_robot)
    print(f"Map with robot saved: maps/test_map_robot.png")
