#!/usr/bin/env python3
"""
Face Animator Module
Generates face animation keyframes for lip-sync and expressions
"""

import logging
import numpy as np
from typing import Dict, List
import random

logger = logging.getLogger(__name__)

class FaceAnimator:
    """Generate face animation keyframes for robot display."""
    
    def __init__(self, config: Dict):
        """Initialize face animator.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.display_config = config.get('display', {})
        
        # Mouth shape definitions (relative size)
        self.mouth_shapes = {
            'closed': {'width': 0.1, 'height': 0.05},
            'narrow': {'width': 0.3, 'height': 0.2},
            'medium': {'width': 0.5, 'height': 0.4},
            'open': {'width': 0.6, 'height': 0.6},
            'round': {'width': 0.4, 'height': 0.5},
        }
        
        # Eye states
        self.eye_states = {
            'normal': {'openness': 1.0},
            'blink': {'openness': 0.0},
            'half': {'openness': 0.5},
            'wide': {'openness': 1.2},
        }
        
        logger.info("Face animator initialized")
    
    def generate_lipsync(self, phoneme_timings: List[Dict], duration: float = None) -> Dict:
        """Generate lip-sync animation from phoneme timings.
        
        Args:
            phoneme_timings: List of phoneme timing dicts from TTS
            duration: Total duration (auto-calculated if None)
        
        Returns:
            Animation data dict with keyframes
        """
        keyframes = []
        
        # Add idle state at start
        keyframes.append({
            'time': 0,
            'mouth': self.mouth_shapes['closed'],
            'eyes': self.eye_states['normal']
        })
        
        # Generate mouth movements from phonemes
        for phoneme in phoneme_timings:
            time = phoneme.get('time', 0)
            shape_name = phoneme.get('shape', 'medium')
            shape = self.mouth_shapes.get(shape_name, self.mouth_shapes['medium'])
            
            keyframes.append({
                'time': time,
                'mouth': shape,
                'eyes': self.eye_states['normal']
            })
        
        # Add random blinks
        if duration:
            keyframes.extend(self._generate_blinks(duration))
        
        # Sort by time
        keyframes.sort(key=lambda k: k['time'])
        
        animation = {
            'keyframes': keyframes,
            'duration': duration or (keyframes[-1]['time'] + 0.5),
            'fps': self.display_config.get('frame_rate', 60)
        }
        
        logger.info(f"Generated lip-sync animation: {len(keyframes)} keyframes, {animation['duration']:.2f}s")
        return animation
    
    def _generate_blinks(self, duration: float, blink_interval: float = 3.0) -> List[Dict]:
        """Generate random eye blinks.
        
        Args:
            duration: Total animation duration
            blink_interval: Average time between blinks
        
        Returns:
            List of blink keyframes
        """
        blinks = []
        current_time = random.uniform(1.0, 2.0)  # First blink
        
        while current_time < duration:
            # Blink start
            blinks.append({
                'time': current_time,
                'mouth': self.mouth_shapes['closed'],
                'eyes': self.eye_states['blink']
            })
            
            # Blink end (0.1s later)
            blinks.append({
                'time': current_time + 0.1,
                'mouth': self.mouth_shapes['closed'],
                'eyes': self.eye_states['normal']
            })
            
            # Next blink
            current_time += random.uniform(blink_interval * 0.5, blink_interval * 1.5)
        
        return blinks
    
    def generate_expression(self, expression: str, duration: float = 2.0) -> Dict:
        """Generate a specific facial expression.
        
        Args:
            expression: Expression name (happy, sad, surprised, angry)
            duration: Expression duration
        
        Returns:
            Animation data dict
        """
        expressions = {
            'happy': {
                'mouth': {'width': 0.7, 'height': 0.4, 'curve': 'smile'},
                'eyes': {'openness': 1.0}
            },
            'sad': {
                'mouth': {'width': 0.5, 'height': 0.2, 'curve': 'frown'},
                'eyes': {'openness': 0.7}
            },
            'surprised': {
                'mouth': {'width': 0.4, 'height': 0.6, 'curve': 'round'},
                'eyes': {'openness': 1.3}
            },
            'angry': {
                'mouth': {'width': 0.6, 'height': 0.3, 'curve': 'straight'},
                'eyes': {'openness': 0.8}
            },
            'neutral': {
                'mouth': self.mouth_shapes['closed'],
                'eyes': self.eye_states['normal']
            }
        }
        
        expr = expressions.get(expression, expressions['neutral'])
        
        keyframes = [
            {'time': 0, 'mouth': expr['mouth'], 'eyes': expr['eyes']},
            {'time': duration, 'mouth': expr['mouth'], 'eyes': expr['eyes']}
        ]
        
        animation = {
            'keyframes': keyframes,
            'duration': duration,
            'fps': self.display_config.get('frame_rate', 60)
        }
        
        logger.info(f"Generated '{expression}' expression: {duration}s")
        return animation
    
    def generate_idle_animation(self, duration: float = 10.0) -> Dict:
        """Generate idle face animation with random blinks.
        
        Args:
            duration: Animation duration
        
        Returns:
            Animation data dict
        """
        keyframes = [
            {
                'time': 0,
                'mouth': self.mouth_shapes['closed'],
                'eyes': self.eye_states['normal']
            }
        ]
        
        # Add random blinks
        keyframes.extend(self._generate_blinks(duration))
        
        # Sort by time
        keyframes.sort(key=lambda k: k['time'])
        
        animation = {
            'keyframes': keyframes,
            'duration': duration,
            'fps': self.display_config.get('frame_rate', 60)
        }
        
        logger.info(f"Generated idle animation: {len(keyframes)} keyframes, {duration}s")
        return animation


if __name__ == "__main__":
    # Test face animator
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    animator = FaceAnimator(config)
    
    # Test lip-sync generation
    print("\nTest 1: Lip-sync animation")
    test_phonemes = [
        {'time': 0.0, 'shape': 'open', 'duration': 0.2},
        {'time': 0.2, 'shape': 'medium', 'duration': 0.15},
        {'time': 0.35, 'shape': 'round', 'duration': 0.2},
        {'time': 0.55, 'shape': 'closed', 'duration': 0.1},
    ]
    
    lipsync = animator.generate_lipsync(test_phonemes, duration=2.0)
    print(f"  Keyframes: {len(lipsync['keyframes'])}")
    print(f"  Duration: {lipsync['duration']}s")
    
    # Test expressions
    print("\nTest 2: Expressions")
    for expr in ['happy', 'sad', 'surprised', 'angry']:
        anim = animator.generate_expression(expr)
        print(f"  {expr}: {len(anim['keyframes'])} keyframes")
    
    # Test idle animation
    print("\nTest 3: Idle animation")
    idle = animator.generate_idle_animation(duration=5.0)
    print(f"  Keyframes: {len(idle['keyframes'])}")
    print(f"  Duration: {idle['duration']}s")
