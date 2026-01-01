"""
Voice Input Module
Speech-to-text conversion using Google Speech Recognition
"""

import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)


class VoiceRecognizer:
    def __init__(self, config):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.language = config.get('speech_language', 'en-IN')
        
        # Adjust for ambient noise
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        logger.info("✓ Voice recognition initialized")
        
    async def recognize(self, audio_data):
        """
        Convert audio to text
        
        Args:
            audio_data: Audio bytes or AudioData object
            
        Returns:
            str: Recognized text
        """
        try:
            # If audio_data is bytes, convert to AudioData
            if isinstance(audio_data, bytes):
                audio = sr.AudioData(audio_data, 16000, 2)
            else:
                audio = audio_data
                
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
            
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
            
    def listen(self):
        """
        Listen from microphone and return audio
        
        Returns:
            AudioData: Captured audio
        """
        with self.mic as source:
            logger.info("Listening...")
            audio = self.recognizer.listen(source, timeout=5)
            return audio
