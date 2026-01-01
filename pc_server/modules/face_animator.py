#!/usr/bin/env python3
"""
Face Animator Module - Lip-Sync Animation Generator

Generates face animation keyframes synchronized with speech phonemes.
Creates eye blink, mouth movements for realistic lip-sync.
"""

import logging
from typing import List, Dict
import random

logger = logging.getLogger(__name__)


class FaceAnimator:
    """Generate face animation keyframes for lip-sync."""
    
    # Phoneme to mouth shape mapping
    PHONEME_SHAPES = {
        'A': 'open',      # ah, a
        'E': 'wide',      # ee, e
        'I': 'smile',     # ih, i
        'O': 'round',     # oh, o
        'U': 'pucker',    # oo, u
        'M': 'closed',    # m, b, p
        'F': 'teeth',     # f, v
        'L': 'tongue',    # l, d, t
        'S': 'hiss',      # s, z
        'R': 'slight',    # r
        'default': 'neutral'
    }
    
    def __init__(self, config: dict):
        """
        Initialize face animator.
        
        Args:
            config: Configuration dictionary with display settings
        """
        self.config = config.get('display', {})
        self.face_size = self.config.get('face_size', 600)
        self.fps = self.config.get('fps', 60)
        self.blink_interval = self.config.get('eye_blink_interval', [3, 7])
        
        logger.info(f"Face animator initialized (size: {self.face_size}, fps: {self.fps})")
    
    def generate_lipsync(self, phonemes: List[Dict], 
                         total_duration: float) -> List[Dict]:
        """
        Generate lip-sync animation keyframes from phonemes.
        
        Args:
            phonemes: List of phoneme dictionaries with timing
            total_duration: Total animation duration in seconds
            
        Returns:
            List of animation keyframes
        """
        keyframes = []
        
        # Add initial neutral frame
        keyframes.append({
            'time': 0,
            'mouth': 'neutral',
            'eyes': 'open'
        })
        
        # Generate mouth shapes from phonemes
        for phoneme in phonemes:
            text = phoneme['text'].upper()
            offset = phoneme['offset']
            
            # Get mouth shape for first letter
            mouth_shape = self._get_mouth_shape(text[0] if text else '')
            
            keyframes.append({
                'time': offset,
                'mouth': mouth_shape,
                'eyes': 'open'
            })
        
        # Add eye blinks
        keyframes = self._add_eye_blinks(keyframes, total_duration)
        
        # Sort by time
        keyframes.sort(key=lambda x: x['time'])
        
        # Add final neutral frame
        keyframes.append({
            'time': total_duration,
            'mouth': 'neutral',
            'eyes': 'open'
        })
        
        logger.debug(f"Generated {len(keyframes)} keyframes")
        return keyframes
    
    def _get_mouth_shape(self, letter: str) -> str:
        """Map letter to mouth shape."""
        for phoneme, shape in self.PHONEME_SHAPES.items():
            if letter in phoneme:
                return shape
        return self.PHONEME_SHAPES['default']
    
    def _add_eye_blinks(self, keyframes: List[Dict], 
                        duration: float) -> List[Dict]:
        """
        Add random eye blink keyframes.
        
        Args:
            keyframes: Existing keyframes
            duration: Total duration
            
        Returns:
            Keyframes with blinks added
        """
        blink_times = []
        current_time = random.uniform(*self.blink_interval)
        
        while current_time < duration:
            blink_times.append(current_time)
            current_time += random.uniform(*self.blink_interval)
        
        # Add blink keyframes
        for blink_time in blink_times:
            # Blink start
            keyframes.append({
                'time': blink_time,
                'eyes': 'closing'
            })
            # Blink end
            keyframes.append({
                'time': blink_time + 0.15,  # 150ms blink
                'eyes': 'open'
            })
        
        return keyframes
    
    def generate_expression(self, emotion: str) -> Dict:
        """
        Generate static expression animation.
        
        Args:
            emotion: Emotion name (happy, sad, surprised, angry)
            
        Returns:
            Expression animation data
        """
        expressions = {
            'happy': {
                'mouth': 'smile',
                'eyes': 'squint',
                'duration': 2.0
            },
            'sad': {
                'mouth': 'frown',
                'eyes': 'droopy',
                'duration': 2.0
            },
            'surprised': {
                'mouth': 'open',
                'eyes': 'wide',
                'duration': 1.5
            },
            'angry': {
                'mouth': 'tight',
                'eyes': 'narrow',
                'duration': 2.0
            },
            'neutral': {
                'mouth': 'neutral',
                'eyes': 'open',
                'duration': 1.0
            }
        }
        
        return expressions.get(emotion, expressions['neutral'])


if __name__ == "__main__":
    # Test face animator
    import yaml
    
    logging.basicConfig(level=logging.DEBUG)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize animator
    animator = FaceAnimator(config)
    
    # Test phonemes
    test_phonemes = [
        {'text': 'Hello', 'offset': 0.0, 'duration': 0.5},
        {'text': 'I', 'offset': 0.5, 'duration': 0.1},
        {'text': 'am', 'offset': 0.6, 'duration': 0.2},
        {'text': 'robot', 'offset': 0.8, 'duration': 0.5},
    ]
    
    print("\n" + "="*60)
    print("FACE ANIMATOR TEST")
    print("="*60 + "\n")
    
    # Generate lip-sync
    keyframes = animator.generate_lipsync(test_phonemes, 2.0)
    
    print(f"Generated {len(keyframes)} keyframes:\n")
    for kf in keyframes[:10]:
        print(f"  t={kf['time']:.3f}s: mouth={kf.get('mouth', 'same')}, eyes={kf.get('eyes', 'same')}")
    
    # Test expression
    print("\n" + "-"*60)
    print("\nHappy expression:")
    happy = animator.generate_expression('happy')
    print(f"  {happy}")
