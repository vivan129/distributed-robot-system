#!/usr/bin/env python3
"""
TTS Engine Module - Edge TTS Integration

Provides text-to-speech synthesis with phoneme timing for lip-sync animation.
Uses Microsoft Edge TTS for high-quality Indian English voices.
"""

import os
import asyncio
import logging
from typing import Tuple, List, Dict
import edge_tts
import tempfile
from datetime import datetime

logger = logging.getLogger(__name__)


class TTSEngine:
    """Text-to-speech engine with phoneme extraction for lip-sync."""
    
    def __init__(self, config: dict):
        """
        Initialize TTS engine.
        
        Args:
            config: Configuration dictionary with TTS settings
        """
        self.config = config.get('tts', {})
        self.voice = self.config.get('voice', 'en-IN-NeerjaNeural')
        self.rate = self.config.get('rate', '+0%')
        self.volume = self.config.get('volume', '+0%')
        
        # Create output directory
        self.output_dir = 'output/audio'
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"TTS Engine initialized with voice: {self.voice}")
    
    async def synthesize_async(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Synthesize speech from text asynchronously.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Tuple of (audio_file_path, phoneme_timings)
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = os.path.join(self.output_dir, f"tts_{timestamp}.mp3")
            
            # Create TTS communication
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # Collect phonemes
            phonemes = []
            
            # Save audio and collect metadata
            with open(audio_path, 'wb') as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Extract phoneme timing
                        phonemes.append({
                            'text': chunk.get('text', ''),
                            'offset': chunk.get('offset', 0) / 10000000,  # Convert to seconds
                            'duration': chunk.get('duration', 0) / 10000000
                        })
            
            logger.info(f"Synthesized audio: {audio_path}")
            logger.debug(f"Phoneme count: {len(phonemes)}")
            
            return audio_path, phonemes
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise
    
    def synthesize(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Synchronous wrapper for synthesize_async.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Tuple of (audio_file_path, phoneme_timings)
        """
        return asyncio.run(self.synthesize_async(text))
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove old audio files."""
        import time
        current_time = time.time()
        
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    os.remove(filepath)
                    logger.debug(f"Deleted old file: {filename}")


if __name__ == "__main__":
    # Test TTS engine
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize TTS
    tts = TTSEngine(config)
    
    # Test synthesis
    test_text = "Hello! I am your robot assistant. I can move forward, backward, left, and right."
    
    print("\n" + "="*60)
    print("TTS ENGINE TEST")
    print("="*60)
    print(f"\nText: {test_text}\n")
    
    audio_path, phonemes = tts.synthesize(test_text)
    
    print(f"Audio saved to: {audio_path}")
    print(f"Phonemes extracted: {len(phonemes)}")
    print("\nFirst 5 phonemes:")
    for p in phonemes[:5]:
        print(f"  {p['text']}: offset={p['offset']:.3f}s, duration={p['duration']:.3f}s")
