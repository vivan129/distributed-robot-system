"""Camera streaming module supporting OpenCV and Picamera2."""

import cv2
import numpy as np
import logging
from typing import Generator, Optional, Tuple
import time

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class CameraStreamer:
    """Stream camera frames with support for multiple camera types."""
    
    def __init__(self, config: dict):
        """Initialize camera based on config.
        
        Args:
            config: Configuration dict with camera settings
        """
        self.config = config
        self.camera_config = config['camera']
        self.camera_type = self.camera_config['type']
        self.camera = None
        self.running = False
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera hardware."""
        try:
            if self.camera_type == 'picamera2' and PICAMERA2_AVAILABLE:
                self._init_picamera2()
            else:
                self._init_opencv()
            
            logger.info(f"✓ Camera initialized: {self.camera_type}")
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            raise
    
    def _init_picamera2(self):
        """Initialize Picamera2 for Raspberry Pi camera module."""
        self.camera = Picamera2()
        
        config = self.camera.create_preview_configuration(
            main={
                'size': (self.camera_config['width'], self.camera_config['height']),
                'format': 'RGB888'
            }
        )
        
        self.camera.configure(config)
        self.camera.start()
        time.sleep(2)  # Camera warm-up
        
        logger.info("Picamera2 started")
    
    def _init_opencv(self):
        """Initialize OpenCV camera (USB webcam or Pi camera via V4L2)."""
        device_index = self.camera_config.get('device_index', 0)
        self.camera = cv2.VideoCapture(device_index)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera at index {device_index}")
        
        # Set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config['width'])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config['height'])
        self.camera.set(cv2.CAP_PROP_FPS, self.camera_config['fps'])
        
        logger.info(f"OpenCV camera started (device {device_index})")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from camera.
        
        Returns:
            np.ndarray: Frame as BGR image, or None if capture failed
        """
        try:
            if self.camera_type == 'picamera2' and PICAMERA2_AVAILABLE:
                frame = self.camera.capture_array()
                # Convert RGB to BGR for OpenCV compatibility
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Failed to capture frame")
                    return None
            
            # Apply transformations
            if self.camera_config.get('flip_horizontal'):
                frame = cv2.flip(frame, 1)
            if self.camera_config.get('flip_vertical'):
                frame = cv2.flip(frame, 0)
            
            return frame
        
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None
    
    def stream_frames(self, quality: int = 80) -> Generator[bytes, None, None]:
        """Stream frames as JPEG bytes.
        
        Args:
            quality: JPEG compression quality (1-100)
        
        Yields:
            bytes: JPEG-encoded frame data
        """
        self.running = True
        logger.info("Starting camera stream...")
        
        while self.running:
            frame = self.capture_frame()
            
            if frame is not None:
                # Encode as JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                success, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                if success:
                    yield buffer.tobytes()
            
            time.sleep(0.033)  # ~30 FPS
    
    def get_frame_jpeg(self, quality: Optional[int] = None) -> Optional[bytes]:
        """Get single frame as JPEG bytes.
        
        Args:
            quality: JPEG quality (1-100). Uses config default if None.
        
        Returns:
            bytes: JPEG-encoded frame, or None if capture failed
        """
        frame = self.capture_frame()
        
        if frame is None:
            return None
        
        if quality is None:
            quality = self.camera_config.get('stream_quality', 80)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, buffer = cv2.imencode('.jpg', frame, encode_param)
        
        return buffer.tobytes() if success else None
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get current camera resolution.
        
        Returns:
            Tuple[int, int]: (width, height)
        """
        return (self.camera_config['width'], self.camera_config['height'])
    
    def stop(self):
        """Stop camera streaming."""
        self.running = False
        logger.info("Camera stream stopped")
    
    def cleanup(self):
        """Release camera resources."""
        logger.info("Releasing camera...")
        self.stop()
        
        try:
            if self.camera_type == 'picamera2' and PICAMERA2_AVAILABLE:
                if self.camera:
                    self.camera.stop()
                    self.camera.close()
            else:
                if self.camera:
                    self.camera.release()
            
            logger.info("✓ Camera released")
        except Exception as e:
            logger.error(f"Camera cleanup error: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.cleanup()
