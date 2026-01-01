#!/usr/bin/env python3
"""
Face Animator Module - Lip-Sync Animation Generator

Generates facial animation keyframes synchronized with speech
for display on the robot's screen.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import random
from typing import Dict, List
import time
import math

logger = logging.getLogger(__name__)


class FaceAnimator:
    """Generate lip-synced face animations for robot display."""
    
    def __init__(self, config: Dict):
        """
        Initialize face animator.
        
        Args:
            config: Display configuration dictionary
        """
        self.config = config.get('display', {})
        
        # Display settings
        self.width = self.config.get('resolution', {}).get('width', 1024)
        self.height = self.config.get('resolution', {}).get('height', 600)
        self.fps = self.config.get('fps', 60)
        
        # Face element sizes
        self.eye_size = self.config.get('eye_size', 80)
        self.mouth_width = self.config.get('mouth_width', 120)
        
        # Colors
        self.bg_color = self.config.get('background_color', [0, 0, 0])
        self.eye_color = self.config.get('eye_color', [255, 255, 255])
        self.mouth_color = self.config.get('mouth_color', [255, 100, 100])
        
        # Blink settings
        self.blink_interval = self.config.get('blink_interval', 3)
        self.last_blink = time.time()
        
        # Viseme mouth shapes
        self.viseme_shapes = self._define_viseme_shapes()
        
        logger.info(f"Face Animator initialized ({self.width}x{self.height} @ {self.fps}fps)")
    
    def _define_viseme_shapes(self) -> Dict[str, Dict]:
        """
        Define mouth shapes for each viseme.
        
        Returns:
            Dictionary of viseme configurations
        """
        return {
            'closed': {
                'type': 'line',
                'width': self.mouth_width * 0.6,
                'height': 5,
                'openness': 0
            },
            'A': {
                'type': 'oval',
                'width': self.mouth_width * 0.8,
                'height': 60,
                'openness': 0.8
            },
            'E': {
                'type': 'wide',
                'width': self.mouth_width,
                'height': 30,
                'openness': 0.5
            },
            'O': {
                'type': 'circle',
                'width': self.mouth_width * 0.6,
                'height': 60,
                'openness': 0.9
            },
            'M': {
                'type': 'line',
                'width': self.mouth_width * 0.5,
                'height': 3,
                'openness': 0
            },
            'F': {
                'type': 'bite',
                'width': self.mouth_width * 0.7,
                'height': 20,
                'openness': 0.3
            },
            'TH': {
                'type': 'tongue',
                'width': self.mouth_width * 0.6,
                'height': 25,
                'openness': 0.4
            },
            'L': {
                'type': 'wide',
                'width': self.mouth_width * 0.8,
                'height': 35,
                'openness': 0.5
            }
        }
    
    def generate_lipsync(self, viseme_timings: List[Dict], duration: float = None) -> List[Dict]:
        """
        Generate lip-sync animation keyframes.
        
        Args:
            viseme_timings: List of viseme timing dictionaries from TTS
            duration: Total animation duration (auto-calculated if None)
        
        Returns:
            List of animation keyframe dictionaries
        """
        if not viseme_timings:
            return self._generate_idle_animation(5.0)
        
        # Calculate total duration
        if duration is None:
            last_viseme = viseme_timings[-1]
            duration = last_viseme['time'] + last_viseme.get('duration', 0.1)
        
        keyframes = []
        
        # Add initial neutral frame
        keyframes.append({
            'time': 0,
            'left_eye': self._generate_eye_state(open_amount=1.0),
            'right_eye': self._generate_eye_state(open_amount=1.0),
            'mouth': self.viseme_shapes['closed']
        })
        
        # Generate keyframes for each viseme
        for i, viseme in enumerate(viseme_timings):
            viseme_type = viseme.get('viseme', 'closed')
            time_offset = viseme.get('time', 0)
            
            # Get mouth shape
            mouth_shape = self.viseme_shapes.get(viseme_type, self.viseme_shapes['closed'])
            
            # Check if blink should occur
            should_blink = self._should_blink(time_offset)
            eye_open = 0.0 if should_blink else 1.0
            
            # Add keyframe
            keyframes.append({
                'time': time_offset,
                'left_eye': self._generate_eye_state(open_amount=eye_open),
                'right_eye': self._generate_eye_state(open_amount=eye_open),
                'mouth': mouth_shape
            })
            
            # Add blink close frame if blinking
            if should_blink:
                keyframes.append({
                    'time': time_offset + 0.05,
                    'left_eye': self._generate_eye_state(open_amount=1.0),
                    'right_eye': self._generate_eye_state(open_amount=1.0),
                    'mouth': mouth_shape
                })
        
        # Add closing frame
        keyframes.append({
            'time': duration,
            'left_eye': self._generate_eye_state(open_amount=1.0),
            'right_eye': self._generate_eye_state(open_amount=1.0),
            'mouth': self.viseme_shapes['closed']
        })
        
        logger.info(f"Generated {len(keyframes)} animation keyframes for {duration:.2f}s")
        return keyframes
    
    def _generate_eye_state(self, open_amount: float = 1.0, 
                           look_x: float = 0.0, look_y: float = 0.0) -> Dict:
        """
        Generate eye state data.
        
        Args:
            open_amount: 0.0 (closed) to 1.0 (fully open)
            look_x: Horizontal look direction (-1.0 to 1.0)
            look_y: Vertical look direction (-1.0 to 1.0)
        
        Returns:
            Eye state dictionary
        """
        return {
            'open': open_amount,
            'size': self.eye_size,
            'look_x': look_x,
            'look_y': look_y,
            'color': self.eye_color
        }
    
    def _should_blink(self, current_time: float) -> bool:
        """
        Determine if eyes should blink at given time.
        
        Args:
            current_time: Current animation time
        
        Returns:
            True if should blink
        """
        time_since_last = current_time - (self.last_blink % 1000)
        if time_since_last > self.blink_interval:
            self.last_blink = current_time
            return random.random() < 0.3  # 30% chance
        return False
    
    def _generate_idle_animation(self, duration: float) -> List[Dict]:
        """
        Generate idle animation (breathing, occasional blinks).
        
        Args:
            duration: Animation duration in seconds
        
        Returns:
            List of keyframe dictionaries
        """
        keyframes = []
        frame_time = 1.0 / 10  # 10 fps for idle
        
        for t in range(int(duration / frame_time)):
            current_time = t * frame_time
            
            # Gentle breathing effect
            breath = 0.95 + 0.05 * math.sin(current_time * 0.5)
            
            # Random blinks
            blink = self._should_blink(current_time)
            eye_open = 0.0 if blink else 1.0
            
            keyframes.append({
                'time': current_time,
                'left_eye': self._generate_eye_state(open_amount=eye_open * breath),
                'right_eye': self._generate_eye_state(open_amount=eye_open * breath),
                'mouth': self.viseme_shapes['closed']
            })
        
        return keyframes
    
    def generate_expression(self, expression: str) -> List[Dict]:
        """
        Generate animation for facial expression.
        
        Args:
            expression: Expression name (happy, sad, surprised, angry)
        
        Returns:
            List of keyframe dictionaries
        """
        expressions = {
            'happy': {
                'eye_open': 0.8,
                'mouth': 'E',  # Wide smile
                'duration': 2.0
            },
            'sad': {
                'eye_open': 0.6,
                'mouth': 'closed',
                'duration': 2.0
            },
            'surprised': {
                'eye_open': 1.2,  # Extra wide
                'mouth': 'O',
                'duration': 1.5
            },
            'angry': {
                'eye_open': 0.5,
                'mouth': 'closed',
                'duration': 2.0
            }
        }
        
        expr_data = expressions.get(expression, expressions['happy'])
        
        return [{
            'time': 0,
            'left_eye': self._generate_eye_state(open_amount=expr_data['eye_open']),
            'right_eye': self._generate_eye_state(open_amount=expr_data['eye_open']),
            'mouth': self.viseme_shapes[expr_data['mouth']]
        }]


if __name__ == "__main__":
    # Test face animator
    import yaml
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    animator = FaceAnimator(config)
    
    # Test with sample visemes
    test_visemes = [
        {'viseme': 'closed', 'time': 0.0, 'duration': 0.1},
        {'viseme': 'A', 'time': 0.1, 'duration': 0.2},
        {'viseme': 'M', 'time': 0.3, 'duration': 0.15},
        {'viseme': 'E', 'time': 0.45, 'duration': 0.2},
        {'viseme': 'O', 'time': 0.65, 'duration': 0.2},
        {'viseme': 'closed', 'time': 0.85, 'duration': 0.1}
    ]
    
    print("\nGenerating lip-sync animation...")
    keyframes = animator.generate_lipsync(test_visemes)
    
    print(f"\nGenerated {len(keyframes)} keyframes")
    print("\nFirst 5 keyframes:")
    for i, kf in enumerate(keyframes[:5]):
        print(f"  {i}: t={kf['time']:.2f}s, mouth={kf['mouth']['type']}, eyes={kf['left_eye']['open']:.2f}")
