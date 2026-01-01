#!/usr/bin/env python3
"""
SLAM Processor Module - Simultaneous Localization and Mapping

Handles map building and robot localization using LiDAR data
from RP-LIDAR A1.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional
import time
import os

logger = logging.getLogger(__name__)


class SLAMProcessor:
    """SLAM processor for robot mapping and localization."""
    
    def __init__(self, config: Dict):
        """
        Initialize SLAM processor.
        
        Args:
            config: SLAM configuration dictionary
        """
        self.config = config
        
        # Map configuration
        map_config = self.config.get('map', {})
        self.map_width = map_config.get('width', 2000)
        self.map_height = map_config.get('height', 2000)
        self.resolution = map_config.get('resolution', 0.05)  # meters per pixel
        
        # Initialize occupancy grid
        self.occupancy_grid = np.ones((self.map_height, self.map_width)) * 0.5
        self.log_odds_grid = np.zeros((self.map_height, self.map_width))
        
        # Robot pose (x, y, theta)
        origin = map_config.get('origin', {'x': 1000, 'y': 1000, 'theta': 0.0})
        self.robot_pose = np.array([
            origin['x'],
            origin['y'],
            origin['theta']
        ])
        
        # Occupancy parameters
        occ_config = self.config.get('occupancy', {})
        self.free_threshold = occ_config.get('free_threshold', 0.3)
        self.occupied_threshold = occ_config.get('occupied_threshold', 0.7)
        self.log_odds_hit = occ_config.get('log_odds_hit', 0.4)
        self.log_odds_miss = occ_config.get('log_odds_miss', -0.4)
        self.log_odds_max = occ_config.get('log_odds_max', 3.5)
        self.log_odds_min = occ_config.get('log_odds_min', -3.5)
        
        # LiDAR parameters
        lidar_config = self.config.get('lidar', {})
        self.range_min = lidar_config.get('range_min', 0.15)
        self.range_max = lidar_config.get('range_max', 12.0)
        
        # Statistics
        self.scan_count = 0
        self.last_update = time.time()
        
        logger.info(f"SLAM Processor initialized ({self.map_width}x{self.map_height}, {self.resolution}m/px)")
    
    def add_scan(self, ranges: List[float], angles: List[float]):
        """
        Add a LiDAR scan to the map.
        
        Args:
            ranges: List of range measurements (meters)
            angles: List of corresponding angles (degrees)
        """
        if len(ranges) != len(angles):
            logger.error("Ranges and angles length mismatch")
            return
        
        # Filter scan data
        filtered_ranges, filtered_angles = self._filter_scan(ranges, angles)
        
        if not filtered_ranges:
            logger.warning("No valid scan points after filtering")
            return
        
        # Update map
        self._update_occupancy_grid(filtered_ranges, filtered_angles)
        
        self.scan_count += 1
        self.last_update = time.time()
        
        if self.scan_count % 10 == 0:
            logger.debug(f"Processed {self.scan_count} scans")
    
    def _filter_scan(self, ranges: List[float], angles: List[float]) -> Tuple[List[float], List[float]]:
        """
        Filter scan data to remove invalid points.
        
        Args:
            ranges: Range measurements
            angles: Angle measurements
        
        Returns:
            Filtered (ranges, angles)
        """
        filtered_ranges = []
        filtered_angles = []
        
        for r, a in zip(ranges, angles):
            # Check range validity
            if self.range_min <= r <= self.range_max:
                filtered_ranges.append(r)
                filtered_angles.append(a)
        
        return filtered_ranges, filtered_angles
    
    def _update_occupancy_grid(self, ranges: List[float], angles: List[float]):
        """
        Update occupancy grid with scan data using ray tracing.
        
        Args:
            ranges: Filtered range measurements
            angles: Filtered angle measurements
        """
        robot_x, robot_y, robot_theta = self.robot_pose
        
        for range_m, angle_deg in zip(ranges, angles):
            # Convert to radians and add robot orientation
            angle_rad = np.radians(angle_deg) + robot_theta
            
            # Calculate endpoint in world coordinates
            end_x = robot_x + (range_m / self.resolution) * np.cos(angle_rad)
            end_y = robot_y + (range_m / self.resolution) * np.sin(angle_rad)
            
            # Ray trace from robot to endpoint
            ray_points = self._bresenham_line(
                int(robot_x), int(robot_y),
                int(end_x), int(end_y)
            )
            
            # Update cells along ray (free space)
            for px, py in ray_points[:-1]:
                if 0 <= px < self.map_width and 0 <= py < self.map_height:
                    self._update_cell(py, px, is_occupied=False)
            
            # Update endpoint (occupied)
            end_px, end_py = int(end_x), int(end_y)
            if 0 <= end_px < self.map_width and 0 <= end_py < self.map_height:
                self._update_cell(end_py, end_px, is_occupied=True)
    
    def _update_cell(self, row: int, col: int, is_occupied: bool):
        """
        Update a single grid cell using log-odds.
        
        Args:
            row: Cell row
            col: Cell column
            is_occupied: True if obstacle detected
        """
        # Update log-odds
        delta = self.log_odds_hit if is_occupied else self.log_odds_miss
        self.log_odds_grid[row, col] = np.clip(
            self.log_odds_grid[row, col] + delta,
            self.log_odds_min,
            self.log_odds_max
        )
        
        # Convert to probability
        self.occupancy_grid[row, col] = 1.0 - (1.0 / (1.0 + np.exp(self.log_odds_grid[row, col])))
    
    def _bresenham_line(self, x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
        """
        Bresenham's line algorithm for ray tracing.
        
        Args:
            x0, y0: Start point
            x1, y1: End point
        
        Returns:
            List of (x, y) points along line
        """
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            points.append((x, y))
            
            if x == x1 and y == y1:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return points
    
    def get_current_map(self) -> np.ndarray:
        """
        Get current occupancy grid map.
        
        Returns:
            Occupancy grid as numpy array
        """
        return self.occupancy_grid.copy()
    
    def get_map_image(self) -> np.ndarray:
        """
        Get map as displayable image.
        
        Returns:
            Map image (grayscale, 0-255)
        """
        # Convert probabilities to grayscale
        map_image = (1.0 - self.occupancy_grid) * 255
        map_image = map_image.astype(np.uint8)
        
        # Draw robot position
        robot_x, robot_y = int(self.robot_pose[0]), int(self.robot_pose[1])
        cv2.circle(map_image, (robot_x, robot_y), 10, 0, -1)
        
        # Draw orientation arrow
        arrow_len = 20
        arrow_x = int(robot_x + arrow_len * np.cos(self.robot_pose[2]))
        arrow_y = int(robot_y + arrow_len * np.sin(self.robot_pose[2]))
        cv2.arrowedLine(map_image, (robot_x, robot_y), (arrow_x, arrow_y), 0, 2)
        
        return map_image
    
    def save_map(self, filepath: str):
        """
        Save map to file.
        
        Args:
            filepath: Output file path (.pgm or .png)
        """
        try:
            map_image = self.get_map_image()
            cv2.imwrite(filepath, map_image)
            logger.info(f"Map saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save map: {e}")
    
    def update_robot_pose(self, x: float, y: float, theta: float):
        """
        Update robot pose (for odometry or localization).
        
        Args:
            x: X position (pixels)
            y: Y position (pixels)
            theta: Orientation (radians)
        """
        self.robot_pose = np.array([x, y, theta])
    
    def get_robot_pose(self) -> Tuple[float, float, float]:
        """
        Get current robot pose.
        
        Returns:
            (x, y, theta) tuple
        """
        return tuple(self.robot_pose)
    
    def reset_map(self):
        """Reset map to unknown state."""
        self.occupancy_grid = np.ones((self.map_height, self.map_width)) * 0.5
        self.log_odds_grid = np.zeros((self.map_height, self.map_width))
        self.scan_count = 0
        logger.info("Map reset")


if __name__ == "__main__":
    # Test SLAM processor
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/slam_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    slam = SLAMProcessor(config)
    
    # Simulate scan data
    print("\nSimulating LiDAR scans...")
    
    for i in range(5):
        # Generate fake scan (square room)
        angles = list(range(0, 360, 1))
        ranges = []
        
        for angle in angles:
            # Simple square room simulation
            if 45 <= angle < 135 or 225 <= angle < 315:
                ranges.append(2.0)  # Side walls
            else:
                ranges.append(3.0)  # Front/back walls
        
        slam.add_scan(ranges, angles)
    
    print(f"\nProcessed {slam.scan_count} scans")
    
    # Save map
    output_path = "test_map.png"
    slam.save_map(output_path)
    print(f"\nMap saved to {output_path}")
