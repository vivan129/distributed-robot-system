#!/usr/bin/env python3
"""
TTS Engine Module - Edge TTS Integration
Handles text-to-speech synthesis with phoneme timing for lip-sync
"""

import os
import asyncio
import logging
import tempfile
from typing import Dict, List, Tuple
import edge_tts
import json

logger = logging.getLogger(__name__)

class TTSEngine:
    """Edge TTS engine with phoneme timing extraction."""
    
    def __init__(self, config: Dict):
        """Initialize TTS Engine.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.voice = config.get('tts', {}).get('voice', 'en-IN-NeerjaNeural')
        self.rate = config.get('tts', {}).get('rate', '+0%')
        self.pitch = config.get('tts', {}).get('pitch', '+0Hz')
        self.volume = config.get('tts', {}).get('volume', '+0%')
        
        # Create audio output directory
        self.audio_dir = os.path.join(os.path.dirname(__file__), '..', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        
        logger.info(f"TTS Engine initialized with voice: {self.voice}")
    
    async def synthesize_async(self, text: str) -> Tuple[str, List[Dict]]:
        """Synthesize speech asynchronously with phoneme timing.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Tuple of (audio_file_path, phoneme_timings)
        """
        try:
            # Generate unique filename
            audio_file = os.path.join(self.audio_dir, f"tts_{hash(text) % 100000}.mp3")
            
            # Create TTS communicate object
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume
            )
            
            phonemes = []
            
            # Stream audio and collect phonemes
            with open(audio_file, 'wb') as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Extract word timing for lip-sync
                        phonemes.append({
                            'text': chunk.get('text', ''),
                            'offset': chunk.get('offset', 0) / 10000000.0,  # Convert to seconds
                            'duration': chunk.get('duration', 0) / 10000000.0
                        })
            
            logger.info(f"TTS generated: {audio_file} with {len(phonemes)} word boundaries")
            return audio_file, phonemes
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise
    
    def synthesize(self, text: str) -> Tuple[str, List[Dict]]:
        """Synchronous wrapper for synthesize_async.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Tuple of (audio_file_path, phoneme_timings)
        """
        return asyncio.run(self.synthesize_async(text))
    
    def get_phoneme_timings(self, text: str, phonemes: List[Dict]) -> List[Dict]:
        """Convert word boundaries to mouth shape timings.
        
        Args:
            text: Original text
            phonemes: Word boundary timings from Edge TTS
        
        Returns:
            List of mouth shape keyframes for animation
        """
        mouth_shapes = []
        
        for phoneme in phonemes:
            word = phoneme['text'].lower()
            offset = phoneme['offset']
            duration = phoneme['duration']
            
            # Map words to mouth shapes (simplified viseme mapping)
            mouth_shape = self._get_mouth_shape(word)
            
            mouth_shapes.append({
                'time': offset,
                'shape': mouth_shape,
                'duration': duration
            })
        
        return mouth_shapes
    
    def _get_mouth_shape(self, word: str) -> str:
        """Map word to basic mouth shape.
        
        Args:
            word: Word to analyze
        
        Returns:
            Mouth shape identifier
        """
        # Simplified mouth shape detection based on vowel sounds
        if not word:
            return 'closed'
        
        first_char = word[0].lower()
        
        # Vowel-based mapping
        if first_char in 'aeiou':
            if first_char in 'ae':
                return 'open'      # Wide open
            elif first_char in 'io':
                return 'round'     # Rounded
            else:
                return 'medium'    # Medium open
        else:
            # Consonants
            if first_char in 'mbp':
                return 'closed'    # Lips together
            elif first_char in 'fv':
                return 'narrow'    # Narrow opening
            else:
                return 'medium'    # Default
    
    def cleanup_old_audio(self, max_files: int = 50):
        """Clean up old audio files to prevent disk filling.
        
        Args:
            max_files: Maximum number of files to keep
        """
        try:
            files = [os.path.join(self.audio_dir, f) for f in os.listdir(self.audio_dir)
                    if f.startswith('tts_') and f.endswith('.mp3')]
            
            if len(files) > max_files:
                # Sort by modification time and remove oldest
                files.sort(key=os.path.getmtime)
                for old_file in files[:len(files) - max_files]:
                    os.remove(old_file)
                    logger.debug(f"Removed old audio file: {old_file}")
        except Exception as e:
            logger.warning(f"Audio cleanup error: {e}")


if __name__ == "__main__":
    # Test the TTS Engine
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    tts = TTSEngine(config)
    
    # Test synthesis
    test_text = "Hello! I am moving forward for three seconds."
    audio_file, phonemes = tts.synthesize(test_text)
    
    print(f"\nAudio file: {audio_file}")
    print(f"Phonemes: {len(phonemes)}")
    
    mouth_shapes = tts.get_phoneme_timings(test_text, phonemes)
    print(f"\nMouth shapes:")
    for shape in mouth_shapes[:5]:  # Show first 5
        print(f"  {shape['time']:.2f}s: {shape['shape']} ({shape['duration']:.2f}s)")
