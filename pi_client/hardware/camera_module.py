#!/usr/bin/env python3
"""
Camera Module - Video Capture Wrapper
Wraps CameraStreamer with simpler interface for main.py
"""

import logging
import base64
from .camera_streamer import CameraStreamer

logger = logging.getLogger(__name__)


class CameraModule:
    """Simplified camera interface for main Pi client."""
    
    def __init__(self, config: dict):
        """
        Initialize camera module.
        
        Args:
            config: Full robot configuration dictionary
        """
        self.streamer = CameraStreamer(config)
        self.config = config.get('camera', {})
        logger.info("Camera module initialized")
    
    def get_frame(self) -> str:
        """
        Get frame as base64-encoded JPEG string.
        
        Returns:
            Base64-encoded JPEG string or empty string on error
        """
        try:
            frame_bytes = self.streamer.get_jpeg_frame()
            if frame_bytes:
                return base64.b64encode(frame_bytes).decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return ""
    
    def capture_frame(self):
        """Get raw frame array (numpy array)."""
        return self.streamer.capture_frame()
    
    def get_jpeg_frame(self):
        """Get JPEG frame bytes."""
        return self.streamer.get_jpeg_frame()
    
    def release(self):
        """Release camera resources."""
        self.streamer.release()
        logger.info("Camera module released")


if __name__ == "__main__":
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    camera = CameraModule(config)
    
    print("Testing camera module...")
    frame = camera.get_frame()
    print(f"Frame captured: {len(frame)} bytes" if frame else "Failed")
    
    camera.release()
