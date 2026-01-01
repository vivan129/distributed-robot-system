#!/usr/bin/env python3
"""
Camera Streamer Module - Video Streaming

Streams camera frames from Raspberry Pi to PC server.
Supports OpenCV, Picamera2, and USB cameras.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import cv2
import numpy as np
import time
from typing import Optional, Generator, Dict
import io

logger = logging.getLogger(__name__)


class CameraStreamer:
    """Camera streaming handler for Raspberry Pi."""
    
    def __init__(self, config: Dict):
        """
        Initialize camera streamer.
        
        Args:
            config: Camera configuration dictionary
        """
        self.config = config.get('camera', {})
        
        # Camera settings
        self.camera_type = self.config.get('type', 'opencv')
        self.width = self.config.get('width', 640)
        self.height = self.config.get('height', 480)
        self.fps = self.config.get('fps', 30)
        self.quality = self.config.get('stream_quality', 85)
        
        # State
        self.camera = None
        self.is_streaming = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        
        # Initialize camera
        self._initialize_camera()
        
        logger.info(f"Camera Streamer initialized ({self.camera_type}: {self.width}x{self.height} @ {self.fps}fps)")
    
    def _initialize_camera(self):
        """Initialize camera based on configured type."""
        try:
            if self.camera_type == 'opencv':
                self._init_opencv_camera()
            elif self.camera_type == 'picamera2':
                self._init_picamera2()
            else:
                raise ValueError(f"Unknown camera type: {self.camera_type}")
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            raise
    
    def _init_opencv_camera(self):
        """Initialize OpenCV camera."""
        self.camera = cv2.VideoCapture(0)
        
        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera")
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
        
        # Verify settings
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"OpenCV camera initialized ({actual_width}x{actual_height})")
    
    def _init_picamera2(self):
        """Initialize Picamera2."""
        try:
            from picamera2 import Picamera2
            
            self.camera = Picamera2()
            
            config = self.camera.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameRate": self.fps}
            )
            
            self.camera.configure(config)
            self.camera.start()
            
            logger.info(f"Picamera2 initialized ({self.width}x{self.height})")
            
        except ImportError:
            raise RuntimeError("Picamera2 not installed. Run: pip install picamera2")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame.
        
        Returns:
            Frame as numpy array or None
        """
        try:
            if self.camera_type == 'opencv':
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    return None
                return frame
            
            elif self.camera_type == 'picamera2':
                frame = self.camera.capture_array()
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None
    
    def encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """
        Encode frame to JPEG.
        
        Args:
            frame: Frame to encode
        
        Returns:
            JPEG bytes or None
        """
        try:
            # Encode to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            result, encoded = cv2.imencode('.jpg', frame, encode_param)
            
            if not result:
                logger.warning("Frame encoding failed")
                return None
            
            return encoded.tobytes()
            
        except Exception as e:
            logger.error(f"Frame encoding error: {e}")
            return None
    
    def stream(self) -> Generator[bytes, None, None]:
        """
        Stream frames continuously.
        
        Yields:
            JPEG encoded frames
        """
        self.is_streaming = True
        
        while self.is_streaming:
            # Capture frame
            frame = self.capture_frame()
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Encode frame
            jpeg_bytes = self.encode_frame(frame)
            
            if jpeg_bytes:
                self.frame_count += 1
                self.last_frame_time = time.time()
                yield jpeg_bytes
            
            # Control frame rate
            time.sleep(1.0 / self.fps)
    
    def get_fps(self) -> float:
        """Calculate current FPS."""
        elapsed = time.time() - self.last_frame_time
        if elapsed > 0:
            return self.frame_count / elapsed
        return 0.0
    
    def stop_streaming(self):
        """Stop streaming."""
        self.is_streaming = False
        logger.info("Camera streaming stopped")
    
    def cleanup(self):
        """Release camera resources."""
        try:
            self.stop_streaming()
            
            if self.camera:
                if self.camera_type == 'opencv':
                    self.camera.release()
                elif self.camera_type == 'picamera2':
                    self.camera.stop()
            
            logger.info("Camera resources released")
            
        except Exception as e:
            logger.error(f"Camera cleanup error: {e}")
    
    def test_camera(self, duration: float = 5.0):
        """Test camera capture."""
        logger.info(f"Testing camera for {duration} seconds...")
        
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            frame = self.capture_frame()
            if frame is not None:
                frame_count += 1
            time.sleep(0.1)
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        
        logger.info(f"Camera test complete: {frame_count} frames in {elapsed:.1f}s ({fps:.1f} fps)")


if __name__ == "__main__":
    # Test camera streamer
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    camera = CameraStreamer(config)
    
    try:
        # Test camera
        camera.test_camera(duration=5.0)
        
        # Save a test frame
        frame = camera.capture_frame()
        if frame is not None:
            cv2.imwrite('test_frame.jpg', frame)
            print("\nTest frame saved to test_frame.jpg")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        camera.cleanup()
