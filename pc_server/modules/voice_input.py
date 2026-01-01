#!/usr/bin/env python3
"""
Voice Input Module - Speech Recognition

Handles audio capture and speech-to-text conversion using
various backends (Google, Whisper, Sphinx).

Author: Distributed Robot System
Date: January 2026
"""

import logging
import speech_recognition as sr
from typing import Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)


class VoiceInput:
    """Speech recognition handler for robot voice control."""
    
    def __init__(self, config: dict, callback: Optional[Callable] = None):
        """
        Initialize voice input.
        
        Args:
            config: Audio configuration dictionary
            callback: Function to call with recognized text
        """
        self.config = config.get('audio', {}).get('microphone', {})
        self.speech_config = config.get('ai', {}).get('speech_recognition', {})
        self.callback = callback
        
        # Initialize recognizer
        self.recognizer = sr.Recognizer()
        
        # Configure recognizer
        self.recognizer.energy_threshold = self.config.get('silence_threshold', 500)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = self.config.get('silence_duration', 1.5)
        
        # Get microphone
        device_index = self.config.get('device_index', None)
        self.microphone = sr.Microphone(device_index=device_index)
        
        # Recognition settings
        self.engine = self.speech_config.get('engine', 'google')
        self.language = self.speech_config.get('language', 'en-IN')
        self.timeout = self.speech_config.get('timeout', 5)
        self.phrase_time_limit = self.speech_config.get('phrase_time_limit', 10)
        
        # State
        self.listening = False
        self.listen_thread = None
        
        # Adjust for ambient noise
        self._calibrate_microphone()
        
        logger.info(f"Voice input initialized (engine: {self.engine}, language: {self.language})")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        try:
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise... (1 second)")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info(f"Microphone calibrated (threshold: {self.recognizer.energy_threshold})")
        except Exception as e:
            logger.error(f"Microphone calibration failed: {e}")
    
    def listen_once(self) -> Optional[str]:
        """
        Listen for a single voice command.
        
        Returns:
            Recognized text or None
        """
        try:
            with self.microphone as source:
                logger.info("Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_time_limit
                )
                
                logger.info("Processing speech...")
                text = self._recognize_speech(audio)
                
                if text:
                    logger.info(f"Recognized: {text}")
                    if self.callback:
                        self.callback(text)
                    return text
                else:
                    logger.warning("No speech recognized")
                    return None
                    
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return None
    
    def _recognize_speech(self, audio) -> Optional[str]:
        """
        Convert audio to text using configured engine.
        
        Args:
            audio: Audio data
        
        Returns:
            Recognized text or None
        """
        try:
            if self.engine == 'google':
                return self.recognizer.recognize_google(audio, language=self.language)
            elif self.engine == 'whisper':
                return self.recognizer.recognize_whisper(audio, language=self.language[:2])
            elif self.engine == 'sphinx':
                return self.recognizer.recognize_sphinx(audio)
            else:
                logger.error(f"Unknown speech engine: {self.engine}")
                return None
                
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def start_continuous_listening(self):
        """Start continuous listening in background thread."""
        if self.listening:
            logger.warning("Already listening")
            return
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self._continuous_listen_loop, daemon=True)
        self.listen_thread.start()
        logger.info("Started continuous listening")
    
    def _continuous_listen_loop(self):
        """Background loop for continuous listening."""
        while self.listening:
            try:
                text = self.listen_once()
                if text and self.callback:
                    self.callback(text)
                time.sleep(0.5)  # Brief pause between listens
            except Exception as e:
                logger.error(f"Continuous listen error: {e}")
                time.sleep(1)
    
    def stop_continuous_listening(self):
        """Stop continuous listening."""
        self.listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=5)
        logger.info("Stopped continuous listening")
    
    def test_microphone(self) -> bool:
        """
        Test if microphone is working.
        
        Returns:
            True if microphone works
        """
        try:
            with self.microphone as source:
                logger.info("Testing microphone...")
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                logger.info("Microphone test successful")
                return True
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False


if __name__ == "__main__":
    # Test voice input
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    def on_speech(text):
        print(f"\n>>> Heard: {text}")
    
    voice = VoiceInput(config, callback=on_speech)
    
    print("\nSay something...")
    voice.listen_once()
    
    print("\nTesting continuous listening (10 seconds)...")
    voice.start_continuous_listening()
    time.sleep(10)
    voice.stop_continuous_listening()
