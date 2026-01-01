"""
SLAM Processor Module
Handles simultaneous localization and mapping from LiDAR data
"""

import numpy as np
import logging
from collections import deque

logger = logging.getLogger(__name__)


class SLAMProcessor:
    """
    Simple grid-based SLAM implementation
    For production, consider using ROS SLAM packages
    """
    
    def __init__(self, config):
        self.config = config
        
        # Map parameters
        self.resolution = 0.05  # meters per pixel
        self.map_size = (2000, 2000)  # pixels
        
        # Initialize map (0.5 = unknown, 0 = free, 1 = occupied)
        self.map = np.ones(self.map_size) * 0.5
        
        # Robot pose [x, y, theta]
        self.pose = np.array([self.map_size[0]//2, self.map_size[1]//2, 0.0])
        
        # Scan history for averaging
        self.scan_history = deque(maxlen=10)
        
        logger.info("✓ SLAM processor initialized")
        
    def add_scan(self, ranges, angles):
        """
        Process LiDAR scan and update map
        
        Args:
            ranges: List of distances (meters)
            angles: List of angles (degrees)
        """
        try:
            # Convert to numpy arrays
            ranges = np.array(ranges)
            angles = np.radians(np.array(angles))
            
            # Filter invalid readings
            valid = (ranges > 0.15) & (ranges < 12.0)
            ranges = ranges[valid]
            angles = angles[valid]
            
            # Update map
            self._update_occupancy_grid(ranges, angles)
            
            # Store in history
            self.scan_history.append({'ranges': ranges, 'angles': angles})
            
        except Exception as e:
            logger.error(f"SLAM scan processing error: {e}")
            
    def _update_occupancy_grid(self, ranges, angles):
        """
        Update occupancy grid with scan data
        """
        x0, y0, theta = self.pose
        
        for r, angle in zip(ranges, angles):
            # Calculate endpoint in map coordinates
            absolute_angle = theta + angle
            dx = r * np.cos(absolute_angle) / self.resolution
            dy = r * np.sin(absolute_angle) / self.resolution
            
            x1 = int(x0 + dx)
            y1 = int(y0 + dy)
            
            # Check bounds
            if 0 <= x1 < self.map_size[0] and 0 <= y1 < self.map_size[1]:
                # Mark endpoint as occupied
                self.map[x1, y1] = min(1.0, self.map[x1, y1] + 0.1)
                
                # Mark line from robot to endpoint as free (ray tracing)
                self._mark_ray_free(x0, y0, x1, y1)
                
    def _mark_ray_free(self, x0, y0, x1, y1):
        """
        Mark cells along ray as free space (Bresenham's algorithm)
        """
        points = self._bresenham_line(int(x0), int(y0), int(x1), int(y1))
        
        for x, y in points[:-1]:  # Exclude endpoint
            if 0 <= x < self.map_size[0] and 0 <= y < self.map_size[1]:
                self.map[x, y] = max(0.0, self.map[x, y] - 0.05)
                
    def _bresenham_line(self, x0, y0, x1, y1):
        """
        Bresenham's line algorithm
        """
        points = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            points.append((x0, y0))
            
            if x0 == x1 and y0 == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
                
        return points
        
    def add_visual_odometry(self, vision_data):
        """
        Incorporate visual odometry from camera
        (Placeholder for future implementation)
        """
        pass
        
    def get_current_map(self):
        """
        Get current map state
        
        Returns:
            dict: Map data for visualization
        """
        # Convert map to displayable format
        map_display = (self.map * 255).astype(np.uint8)
        
        return {
            'map': map_display.tolist(),
            'robot_pose': self.pose.tolist(),
            'resolution': self.resolution
        }
        
    def save_map(self, filename):
        """
        Save map to file
        """
        try:
            np.save(filename, self.map)
            logger.info(f"Map saved to {filename}")
        except Exception as e:
            logger.error(f"Map save error: {e}")
