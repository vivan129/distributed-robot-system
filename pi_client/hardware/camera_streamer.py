#!/usr/bin/env python3
"""
Camera Streamer Module
Handles camera capture and streaming to PC server
"""

import logging
import cv2
import numpy as np
import asyncio
from typing import Dict, Optional, AsyncGenerator
import time

logger = logging.getLogger(__name__)

class CameraStreamer:
    """Camera capture and streaming."""
    
    def __init__(self, config: Dict):
        """Initialize camera streamer.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.camera_config = config.get('camera', {})
        
        self.camera_type = self.camera_config.get('type', 'opencv')
        self.width = self.camera_config.get('width', 640)
        self.height = self.camera_config.get('height', 480)
        self.fps = self.camera_config.get('fps', 30)
        self.quality = self.camera_config.get('stream_quality', 85)
        
        self.camera = None
        self.is_streaming = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        
        self._init_camera()
    
    def _init_camera(self):
        """Initialize camera based on type."""
        try:
            if self.camera_type == 'opencv':
                device_id = self.camera_config.get('device_id', 0)
                self.camera = cv2.VideoCapture(device_id)
                
                # Set resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, self.fps)
                
                if not self.camera.isOpened():
                    raise RuntimeError("Failed to open camera")
                
                logger.info(f"OpenCV camera initialized: {self.width}x{self.height} @ {self.fps}fps")
            
            elif self.camera_type == 'picamera2':
                try:
                    from picamera2 import Picamera2
                    self.camera = Picamera2()
                    config = self.camera.create_preview_configuration(
                        main={"size": (self.width, self.height)}
                    )
                    self.camera.configure(config)
                    self.camera.start()
                    logger.info(f"Picamera2 initialized: {self.width}x{self.height}")
                except ImportError:
                    logger.error("Picamera2 not available, falling back to OpenCV")
                    self.camera_type = 'opencv'
                    self._init_camera()
            
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            raise
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame.
        
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
                return frame
            
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None
    
    def encode_frame_jpeg(self, frame: np.ndarray) -> Optional[bytes]:
        """Encode frame as JPEG.
        
        Args:
            frame: Frame as numpy array
        
        Returns:
            JPEG bytes or None
        """
        try:
            _, buffer = cv2.imencode(
                '.jpg',
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            )
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Frame encoding error: {e}")
            return None
    
    async def stream(self) -> AsyncGenerator[Dict, None]:
        """Stream frames asynchronously.
        
        Yields:
            Dictionary with frame data and metadata
        """
        self.is_streaming = True
        logger.info("Camera streaming started")
        
        while self.is_streaming:
            try:
                # Capture frame
                frame = self.capture_frame()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Encode as JPEG
                jpeg_bytes = self.encode_frame_jpeg(frame)
                if jpeg_bytes is None:
                    continue
                
                # Calculate FPS
                current_time = time.time()
                fps = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time else 0
                self.last_frame_time = current_time
                self.frame_count += 1
                
                # Yield frame data
                yield {
                    'frame': jpeg_bytes,
                    'timestamp': current_time,
                    'frame_number': self.frame_count,
                    'fps': fps,
                    'width': self.width,
                    'height': self.height
                }
                
                # Control frame rate
                await asyncio.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                await asyncio.sleep(0.1)
        
        logger.info("Camera streaming stopped")
    
    def stop_streaming(self):
        """Stop camera streaming."""
        self.is_streaming = False
    
    def release(self):
        """Release camera resources."""
        try:
            logger.info("Releasing camera...")
            self.stop_streaming()
            
            if self.camera_type == 'opencv' and self.camera:
                self.camera.release()
            elif self.camera_type == 'picamera2' and self.camera:
                self.camera.stop()
            
            logger.info("Camera released")
        except Exception as e:
            logger.error(f"Camera release error: {e}")
    
    def get_status(self) -> Dict:
        """Get camera status.
        
        Returns:
            Status dictionary
        """
        return {
            'is_streaming': self.is_streaming,
            'camera_type': self.camera_type,
            'resolution': f"{self.width}x{self.height}",
            'fps': self.fps,
            'frame_count': self.frame_count
        }


if __name__ == "__main__":
    # Test camera streamer
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    camera = CameraStreamer(config)
    
    try:
        print("\nCapturing 10 frames...")
        for i in range(10):
            frame = camera.capture_frame()
            if frame is not None:
                print(f"Frame {i+1}: {frame.shape}")
            time.sleep(0.5)
        
        print("\nTest complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        camera.release()
