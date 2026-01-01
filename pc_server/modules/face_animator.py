"""
Face Animation Module
Generates keyframe data for lip-synced face display
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FaceKeyframe:
    timestamp: float
    mouth_shape: str
    mouth_width: float
    mouth_height: float
    eye_openness: float


class FaceAnimator:
    """
    Generate dynamic face animations with lip-sync
    Based on phoneme-to-viseme mapping
    """
    
    # Phoneme to mouth shape mapping
    PHONEME_MAP = {
        'AA': ('A', 0.9, 0.8), 'AE': ('A', 0.8, 0.6),
        'AH': ('A', 0.7, 0.5), 'AO': ('O', 0.6, 0.8),
        'AW': ('O', 0.7, 0.7), 'AY': ('A', 0.8, 0.5),
        'EH': ('E', 0.9, 0.4), 'ER': ('E', 0.7, 0.4),
        'EY': ('E', 0.9, 0.3), 'IH': ('I', 0.6, 0.3),
        'IY': ('I', 0.8, 0.2), 'OW': ('O', 0.6, 0.9),
        'OY': ('O', 0.7, 0.7), 'UH': ('U', 0.5, 0.6),
        'UW': ('U', 0.4, 0.8), 'M': ('M', 0.0, 0.0),
        'P': ('M', 0.0, 0.0), 'B': ('M', 0.0, 0.0),
        'F': ('F', 0.7, 0.2), 'V': ('F', 0.7, 0.2),
        'SIL': ('closed', 0.0, 0.0)
    }
    
    def __init__(self, config):
        self.config = config
        self.blink_interval = 3.0  # seconds
        logger.info("✓ Face animator initialized")
        
    def generate_lipsync(self, phoneme_timings: List[Dict]) -> Dict:
        """
        Generate face animation from phoneme timing data
        
        Args:
            phoneme_timings: [{'phoneme': 'AA', 'start': 0.1, 'end': 0.3}, ...]
            
        Returns:
            {'keyframes': [...], 'duration': 2.5}
        """
        if not phoneme_timings:
            return {'keyframes': [], 'duration': 0}
            
        keyframes = []
        
        for pt in phoneme_timings:
            phoneme = pt['phoneme']
            start = pt['start']
            end = pt['end']
            
            # Map phoneme to mouth shape
            mouth_shape, width, height = self.PHONEME_MAP.get(
                phoneme, ('closed', 0.0, 0.0)
            )
            
            # Create keyframes with interpolation
            keyframes.append(FaceKeyframe(
                timestamp=start,
                mouth_shape=mouth_shape,
                mouth_width=width,
                mouth_height=height,
                eye_openness=1.0
            ))
            
            # Hold shape until end
            keyframes.append(FaceKeyframe(
                timestamp=end,
                mouth_shape=mouth_shape,
                mouth_width=width * 0.8,  # Slight decay
                mouth_height=height * 0.8,
                eye_openness=1.0
            ))
            
        # Add blinks
        duration = phoneme_timings[-1]['end'] if phoneme_timings else 1.0
        keyframes = self._add_blinks(keyframes, duration)
        
        # Convert to JSON-serializable format
        result = {
            'keyframes': [
                {
                    'time': kf.timestamp,
                    'mouth': kf.mouth_shape,
                    'mouth_w': kf.mouth_width,
                    'mouth_h': kf.mouth_height,
                    'eyes': kf.eye_openness
                }
                for kf in sorted(keyframes, key=lambda x: x.timestamp)
            ],
            'duration': duration
        }
        
        logger.info(f"Generated {len(result['keyframes'])} keyframes, duration: {duration:.2f}s")
        return result
        
    def _add_blinks(self, keyframes: List[FaceKeyframe], duration: float):
        """
        Add natural blinking to animation
        """
        blink_times = np.arange(0, duration, self.blink_interval)
        blink_times += np.random.uniform(-0.5, 0.5, len(blink_times))
        
        for t in blink_times:
            if 0 < t < duration:
                # Blink: close (0.1s) then open (0.1s)
                keyframes.append(FaceKeyframe(t, 'closed', 0, 0, 0.0))
                keyframes.append(FaceKeyframe(t+0.1, 'closed', 0, 0, 1.0))
                
        return keyframes
        
    def generate_expression(self, emotion='neutral'):
        """
        Generate static expression
        
        Args:
            emotion: 'happy', 'sad', 'surprised', 'angry', 'neutral'
        """
        expressions = {
            'happy': {'mouth': 'A', 'mouth_w': 0.8, 'mouth_h': 0.6, 'eyes': 0.9},
            'sad': {'mouth': 'closed', 'mouth_w': 0.5, 'mouth_h': 0.2, 'eyes': 0.6},
            'surprised': {'mouth': 'O', 'mouth_w': 0.7, 'mouth_h': 0.9, 'eyes': 1.0},
            'angry': {'mouth': 'closed', 'mouth_w': 0.6, 'mouth_h': 0.1, 'eyes': 0.7},
            'neutral': {'mouth': 'closed', 'mouth_w': 0.0, 'mouth_h': 0.0, 'eyes': 1.0}
        }
        
        expr = expressions.get(emotion, expressions['neutral'])
        
        return {
            'keyframes': [{'time': 0, **expr}],
            'duration': 0
        }
