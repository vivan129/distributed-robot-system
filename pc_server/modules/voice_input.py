#!/usr/bin/env python3
"""
Voice Input Module - Speech Recognition

Handles voice input capture and speech-to-text conversion.
Supports multiple backends: Google Speech Recognition, Whisper.
"""

import logging
import io
from typing import Optional
import speech_recognition as sr

logger = logging.getLogger(__name__)


class VoiceInput:
    """Voice input handler for speech recognition."""
    
    def __init__(self, config: dict):
        """
        Initialize voice input system.
        
        Args:
            config: Configuration dictionary with audio settings
        """
        self.config = config.get('audio', {})
        self.recognizer = sr.Recognizer()
        
        # Adjust recognition parameters
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        logger.info("Voice input initialized")
    
    def recognize_from_audio_data(self, audio_data: bytes, 
                                   sample_rate: int = 16000) -> Optional[str]:
        """
        Recognize speech from raw audio data.
        
        Args:
            audio_data: Raw audio bytes
            sample_rate: Audio sample rate
            
        Returns:
            Recognized text or None
        """
        try:
            # Convert bytes to AudioData
            audio = sr.AudioData(
                audio_data,
                sample_rate=sample_rate,
                sample_width=2  # 16-bit audio
            )
            
            # Recognize using Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
            
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None
    
    def recognize_from_microphone(self, timeout: int = 5) -> Optional[str]:
        """
        Capture and recognize speech from microphone.
        
        Args:
            timeout: Recording timeout in seconds
            
        Returns:
            Recognized text or None
        """
        try:
            with sr.Microphone() as source:
                logger.info("Listening...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for speech
                audio = self.recognizer.listen(source, timeout=timeout)
                
                # Recognize
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text
                
        except sr.WaitTimeoutError:
            logger.warning("Listening timeout")
            return None
        except sr.UnknownValueError:
            logger.warning("Speech not understood")
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None


if __name__ == "__main__":
    # Test voice input
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize voice input
    voice = VoiceInput(config)
    
    print("\n" + "="*60)
    print("VOICE INPUT TEST")
    print("="*60)
    print("\nSpeak into your microphone...\n")
    
    # Test microphone input
    text = voice.recognize_from_microphone()
    
    if text:
        print(f"\n✅ Recognized: {text}")
    else:
        print("\n❌ No speech recognized")
