"""
Text-to-Speech Engine
Generates speech with phoneme timing for lip-sync
"""

import edge_tts
import logging
import os
import json
import re

logger = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self, config):
        self.voice = config.get('tts_voice', 'en-IN-NeerjaNeural')
        self.output_dir = '/tmp'
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"✓ TTS engine initialized (voice: {self.voice})")
        
    async def synthesize(self, text):
        """
        Generate speech audio with phoneme timings
        
        Args:
            text: Text to speak
            
        Returns:
            tuple: (audio_file_path, phoneme_timings)
            phoneme_timings = [{'phoneme': 'AA', 'start': 0.1, 'end': 0.3}, ...]
        """
        try:
            audio_path = os.path.join(self.output_dir, 'robot_speech.mp3')
            
            # Generate speech
            communicate = edge_tts.Communicate(text, self.voice)
            
            # Save with subtitle data (contains timing)
            subtitle_path = audio_path.replace('.mp3', '.vtt')
            
            await communicate.save(audio_path)
            
            # Parse phoneme timings from subtitle if available
            phoneme_timings = self._extract_phonemes(text)
            
            logger.info(f"TTS generated: {len(phoneme_timings)} phonemes")
            return audio_path, phoneme_timings
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None, []
            
    def _extract_phonemes(self, text):
        """
        Generate phoneme timing estimates from text
        (Simplified - in production, use proper phoneme extraction)
        """
        # Simplified phoneme mapping
        phoneme_map = {
            'a': 'AA', 'e': 'EH', 'i': 'IY', 'o': 'OW', 'u': 'UW',
            'm': 'M', 'p': 'P', 'b': 'B', 'f': 'F', 'v': 'V',
            ' ': 'SIL'
        }
        
        phonemes = []
        time = 0.0
        
        for char in text.lower():
            phoneme = phoneme_map.get(char, 'AA')
            duration = 0.15 if phoneme != 'SIL' else 0.1
            
            phonemes.append({
                'phoneme': phoneme,
                'start': time,
                'end': time + duration
            })
            
            time += duration
            
        return phonemes
