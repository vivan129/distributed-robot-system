#!/usr/bin/env python3
"""
Text-to-Speech Engine - Edge TTS with Phoneme Timing

Generates speech audio from text with phoneme-level timing
for lip-sync animation.

Author: Distributed Robot System
Date: January 2026
"""

import logging
import asyncio
import edge_tts
import os
import json
import tempfile
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class TTSEngine:
    """Text-to-Speech engine with phoneme timing for lip-sync."""
    
    def __init__(self, config: Dict):
        """
        Initialize TTS engine.
        
        Args:
            config: TTS configuration dictionary
        """
        self.config = config.get('ai', {}).get('tts', {})
        
        # Voice settings
        self.voice = self.config.get('voice', 'en-IN-NeerjaNeural')
        self.rate = self.config.get('rate', '+0%')
        self.volume = self.config.get('volume', '+0%')
        
        # Output directory
        self.output_dir = 'audio_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Phoneme to viseme mapping (for lip-sync)
        self.phoneme_to_viseme = self._build_phoneme_map()
        
        logger.info(f"TTS Engine initialized (voice: {self.voice})")
    
    def _build_phoneme_map(self) -> Dict[str, str]:
        """
        Build phoneme to viseme mapping.
        
        Returns:
            Dictionary mapping phonemes to mouth shapes
        """
        return {
            # Closed/rest
            'sil': 'closed',
            'pau': 'closed',
            
            # A shapes (open)
            'AA': 'A', 'AE': 'A', 'AH': 'A', 'AO': 'A', 'AW': 'A', 'AY': 'A',
            
            # E shapes (wide)
            'EH': 'E', 'ER': 'E', 'EY': 'E', 'IH': 'E', 'IY': 'E',
            
            # O shapes (round)
            'OW': 'O', 'OY': 'O', 'UH': 'O', 'UW': 'O',
            
            # M/B/P (closed lips)
            'M': 'M', 'B': 'M', 'P': 'M',
            
            # F/V (teeth on lip)
            'F': 'F', 'V': 'F',
            
            # TH (tongue between teeth)
            'TH': 'TH', 'DH': 'TH',
            
            # L (tongue tip)
            'L': 'L',
            
            # Default
            'default': 'closed'
        }
    
    async def synthesize_async(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Synthesize speech from text asynchronously.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Tuple of (audio file path, phoneme timings list)
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = os.path.join(self.output_dir, f"speech_{timestamp}.mp3")
            
            # Create TTS communicate object
            communicate = edge_tts.Communicate(
                text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # Save audio and get metadata
            phonemes = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    with open(audio_path, "ab") as f:
                        f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # Extract timing information
                    phonemes.append({
                        'text': chunk.get('text', ''),
                        'offset': chunk.get('offset', 0) / 10000000,  # Convert to seconds
                        'duration': chunk.get('duration', 0) / 10000000
                    })
            
            # Generate viseme timings
            viseme_timings = self._generate_viseme_timings(phonemes)
            
            logger.info(f"Synthesized: {text[:50]}... -> {audio_path}")
            logger.debug(f"Generated {len(viseme_timings)} viseme keyframes")
            
            return audio_path, viseme_timings
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None, []
    
    def synthesize(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Synchronous wrapper for synthesize.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Tuple of (audio file path, phoneme timings list)
        """
        return asyncio.run(self.synthesize_async(text))
    
    def _generate_viseme_timings(self, phonemes: List[Dict]) -> List[Dict]:
        """
        Generate viseme timings from phoneme data.
        
        Args:
            phonemes: List of phoneme dictionaries
        
        Returns:
            List of viseme timing dictionaries
        """
        visemes = []
        
        for phoneme in phonemes:
            # Extract phoneme from text (simplified)
            text = phoneme.get('text', '').upper()
            
            # Determine viseme
            viseme = 'closed'
            for char in text:
                if char in 'AEIOU':
                    if char in 'AE':
                        viseme = 'A'
                    elif char in 'EI':
                        viseme = 'E'
                    else:
                        viseme = 'O'
                    break
                elif char in 'MBP':
                    viseme = 'M'
                    break
                elif char in 'FV':
                    viseme = 'F'
                    break
            
            visemes.append({
                'viseme': viseme,
                'time': phoneme.get('offset', 0),
                'duration': phoneme.get('duration', 0.1)
            })
        
        # Add closing viseme
        if visemes:
            last_time = visemes[-1]['time'] + visemes[-1]['duration']
            visemes.append({
                'viseme': 'closed',
                'time': last_time,
                'duration': 0.1
            })
        
        return visemes
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove old audio files."""
        import time
        
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                age = now - os.path.getmtime(filepath)
                if age > max_age_seconds:
                    os.remove(filepath)
                    logger.debug(f"Removed old audio file: {filename}")


if __name__ == "__main__":
    # Test TTS engine
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    tts = TTSEngine(config)
    
    # Test synthesis
    test_text = "Hello! I am a friendly robot. I can move forward, backward, left, and right."
    
    print(f"\nSynthesizing: {test_text}")
    audio_path, visemes = tts.synthesize(test_text)
    
    if audio_path:
        print(f"\nAudio saved to: {audio_path}")
        print(f"Generated {len(visemes)} viseme keyframes")
        print(f"\nFirst 5 visemes:")
        for viseme in visemes[:5]:
            print(f"  {viseme['time']:.2f}s: {viseme['viseme']} ({viseme['duration']:.2f}s)")
