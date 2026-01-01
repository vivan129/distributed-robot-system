#!/usr/bin/env python3
"""
Voice Input Module - Speech Recognition
Handles audio capture and speech-to-text conversion
"""

import logging
import speech_recognition as sr
from typing import Dict, Optional
import threading
import queue

logger = logging.getLogger(__name__)

class VoiceInput:
    """Speech recognition using Google Speech Recognition."""
    
    def __init__(self, config: Dict):
        """Initialize voice input system.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.listening = False
        self.audio_queue = queue.Queue()
        
        # Get microphone device
        device_index = config.get('audio', {}).get('microphone', {}).get('device_index')
        
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info(f"Voice input initialized with device: {device_index or 'default'}")
            
        except Exception as e:
            logger.error(f"Microphone initialization error: {e}")
            raise
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for a single speech command.
        
        Args:
            timeout: Maximum time to wait for speech (seconds)
        
        Returns:
            Recognized text or None
        """
        try:
            with self.microphone as source:
                logger.info("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            logger.info("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.debug("No speech detected (timeout)")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def start_continuous_listening(self, callback):
        """Start continuous listening in background thread.
        
        Args:
            callback: Function to call with recognized text
        """
        if self.listening:
            logger.warning("Already listening")
            return
        
        self.listening = True
        
        def listen_loop():
            """Background listening loop."""
            logger.info("Started continuous listening")
            
            with self.microphone as source:
                while self.listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        
                        # Recognize in separate thread to avoid blocking
                        threading.Thread(
                            target=self._process_audio,
                            args=(audio, callback),
                            daemon=True
                        ).start()
                        
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        if self.listening:
                            logger.error(f"Listening error: {e}")
                        break
            
            logger.info("Stopped continuous listening")
        
        # Start listening thread
        threading.Thread(target=listen_loop, daemon=True).start()
    
    def _process_audio(self, audio, callback):
        """Process audio in background.
        
        Args:
            audio: Audio data
            callback: Function to call with result
        """
        try:
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            callback(text)
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
    
    def stop_continuous_listening(self):
        """Stop continuous listening."""
        self.listening = False
        logger.info("Stopping continuous listening...")
    
    @staticmethod
    def list_microphones():
        """List available microphone devices.
        
        Returns:
            List of microphone names
        """
        return sr.Microphone.list_microphone_names()


if __name__ == "__main__":
    # Test voice input
    import yaml
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    # List available microphones
    print("\nAvailable microphones:")
    for i, name in enumerate(VoiceInput.list_microphones()):
        print(f"  {i}: {name}")
    
    with open('config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    voice = VoiceInput(config)
    
    # Test single listen
    print("\nTest 1: Single listen (speak something in 5 seconds)...")
    text = voice.listen_once(timeout=5)
    print(f"Result: {text}")
    
    # Test continuous listening
    print("\nTest 2: Continuous listening (speak multiple times, Ctrl+C to stop)...")
    
    def on_speech(text):
        print(f">>> Heard: {text}")
    
    voice.start_continuous_listening(on_speech)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        voice.stop_continuous_listening()
        print("\nStopped.")
