#!/usr/bin/env python3
"""
Camera Streamer Module - Video Streaming

Streams camera frames to PC server.
Supports OpenCV and Picamera2 backends.
"""

import logging
import cv2
import numpy as np
from typing import Generator, Optional
import asyncio

logger = logging.getLogger(__name__)


class CameraStreamer:
    """Camera frame streamer."""
    
    def __init__(self, config: dict):
        """
        Initialize camera streamer.
        
        Args:
            config: Configuration dictionary with camera settings
        """
        camera_config = config.get('camera', {})
        self.camera_type = camera_config.get('type', 'opencv')
        self.width = camera_config.get('width', 640)
        self.height = camera_config.get('height', 480)
        self.fps = camera_config.get('fps', 30)
        self.quality = camera_config.get('stream_quality', 80)
        
        self.camera = None
        self.is_streaming = False
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera based on type."""
        try:
            if self.camera_type == 'opencv':
                self._init_opencv()
            elif self.camera_type == 'picamera2':
                self._init_picamera2()
            else:
                raise ValueError(f"Unknown camera type: {self.camera_type}")
            
            logger.info(f"Camera initialized: {self.camera_type} ({self.width}x{self.height})")
        
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            raise
    
    def _init_opencv(self):
        """Initialize OpenCV camera."""
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera")
        
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
    
    def _init_picamera2(self):
        """Initialize Picamera2."""
        try:
            from picamera2 import Picamera2
            
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": (self.width, self.height)}
            )
            self.camera.configure(config)
            self.camera.start()
        
        except ImportError:
            raise RuntimeError("Picamera2 not installed")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture single frame."""
        try:
            if self.camera_type == 'opencv':
                ret, frame = self.camera.read()
                return frame if ret else None
            
            elif self.camera_type == 'picamera2':
                frame = self.camera.capture_array()
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None
    
    def get_jpeg_frame(self) -> Optional[bytes]:
        """Get frame as JPEG bytes."""
        frame = self.capture_frame()
        
        if frame is None:
            return None
        
        try:
            _, buffer = cv2.imencode('.jpg', frame, 
                                    [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            return buffer.tobytes()
        
        except Exception as e:
            logger.error(f"JPEG encoding error: {e}")
            return None
    
    async def stream_frames(self, callback) -> None:
        """Stream frames asynchronously."""
        self.is_streaming = True
        frame_delay = 1.0 / self.fps
        
        logger.info(f"Started streaming at {self.fps} FPS")
        
        try:
            while self.is_streaming:
                frame_data = self.get_jpeg_frame()
                
                if frame_data:
                    await callback(frame_data)
                
                await asyncio.sleep(frame_delay)
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        
        finally:
            logger.info("Stopped streaming")
    
    def stop_streaming(self):
        """Stop streaming."""
        self.is_streaming = False
    
    def release(self):
        """Release camera resources."""
        try:
            self.stop_streaming()
            
            if self.camera_type == 'opencv' and self.camera:
                self.camera.release()
            elif self.camera_type == 'picamera2' and self.camera:
                self.camera.stop()
            
            logger.info("Camera released")
        
        except Exception as e:
            logger.error(f"Camera release error: {e}")


if __name__ == "__main__":
    # Test camera streamer
    import yaml
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize camera
    camera = CameraStreamer(config)
    
    print("\n" + "="*60)
    print("CAMERA STREAMER TEST")
    print("="*60 + "\n")
    
    try:
        print("Capturing test frames...\n")
        
        for i in range(5):
            frame_data = camera.get_jpeg_frame()
            if frame_data:
                print(f"Frame {i+1}: {len(frame_data)} bytes")
            else:
                print(f"Frame {i+1}: Failed")
            time.sleep(0.5)
        
        print("\nTest complete!")
    
    except KeyboardInterrupt:
        print("\nTest interrupted")
    
    finally:
        camera.release()
