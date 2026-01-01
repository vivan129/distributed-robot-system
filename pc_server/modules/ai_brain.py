#!/usr/bin/env python3
"""
AI Brain Module - Google Gemini Integration (NEW SDK)

Handles natural language processing, command interpretation,
and intelligent conversation using Google Gemini AI.

REQUIRES: Python 3.9+ and google-genai package
"""

import os
import re
import logging
from typing import Dict, Tuple, Optional, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIBrain:
    """AI brain for robot control and conversation using Gemini."""
    
    def __init__(self, config: dict):
        """
        Initialize AI brain with Gemini API.
        
        Args:
            config: Configuration dictionary with AI settings
        """
        self.config = config.get('ai', {})
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize client with NEW SDK
        self.client = genai.Client(api_key=self.api_key)
        
        # Model configuration
        self.model_name = self.config.get('model', 'gemini-2.0-flash-exp')
        self.generation_config = types.GenerateContentConfig(
            temperature=self.config.get('temperature', 0.7),
            max_output_tokens=self.config.get('max_tokens', 1024),
        )
        
        # System prompt
        self.system_prompt = self.config.get('system_prompt', '')
        
        # Chat history (manual management with new SDK)
        self.chat_history: List[Dict[str, str]] = []
        
        # Movement command patterns
        self.movement_patterns = {
            'forward': re.compile(r'\b(forward|ahead|straight)\b', re.IGNORECASE),
            'backward': re.compile(r'\b(backward|back|reverse)\b', re.IGNORECASE),
            'left': re.compile(r'\b(left|port)\b', re.IGNORECASE),
            'right': re.compile(r'\b(right|starboard)\b', re.IGNORECASE),
            'stop': re.compile(r'\b(stop|halt|brake)\b', re.IGNORECASE),
        }
        
        logger.info(f"AI Brain initialized with NEW SDK - model: {self.model_name}")
    
    def process(self, user_input: str) -> Tuple[str, Optional[Dict]]:
        """
        Process user input and generate response with optional movement command.
        
        Args:
            user_input: User's text input
            
        Returns:
            Tuple of (response_text, movement_command_dict or None)
        """
        try:
            # Check for movement commands
            movement_cmd = self._extract_movement_command(user_input)
            
            # Build conversation context
            contents = []
            
            # Add system prompt as first message
            if self.system_prompt and not self.chat_history:
                contents.append(self.system_prompt)
            
            # Add chat history
            for msg in self.chat_history[-10:]:
                role_prefix = "User" if msg['role'] == 'user' else "Assistant"
                contents.append(f"{role_prefix}: {msg['content']}")
            
            # Add current user input
            contents.append(f"User: {user_input}")
            
            # Join all context
            full_prompt = "\n\n".join(contents)
            
            # Generate AI response using NEW SDK
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.generation_config
            )
            
            response_text = response.text.strip()
            
            # Update chat history
            self.chat_history.append({'role': 'user', 'content': user_input})
            self.chat_history.append({'role': 'assistant', 'content': response_text})
            
            # Keep only last 20 messages to prevent context overflow
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            logger.info(f"User: {user_input}")
            logger.info(f"Robot: {response_text}")
            logger.info(f"Movement: {movement_cmd}")
            
            return response_text, movement_cmd
            
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            return "I'm having trouble processing that. Could you try again?", None
    
    def _extract_movement_command(self, text: str) -> Optional[Dict]:
        """
        Extract movement command from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Movement command dictionary or None
        """
        text_lower = text.lower()
        
        # Check for stop command first
        if self.movement_patterns['stop'].search(text_lower):
            return {'direction': 'stop', 'duration': 0}
        
        # Check for directional commands
        direction = None
        for dir_name, pattern in self.movement_patterns.items():
            if dir_name != 'stop' and pattern.search(text_lower):
                direction = dir_name
                break
        
        if not direction:
            return None
        
        # Extract duration
        duration = self._extract_duration(text_lower)
        
        return {
            'direction': direction,
            'duration': duration
        }
    
    def _extract_duration(self, text: str) -> float:
        """
        Extract duration from text (e.g., "3 seconds", "for 5 sec").
        
        Args:
            text: Input text
            
        Returns:
            Duration in seconds (default: 2.0)
        """
        # Pattern: number followed by time unit
        duration_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:second|sec|s)\b', re.IGNORECASE)
        match = duration_pattern.search(text)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Default duration
        return 2.0
    
    def reset_conversation(self):
        """Reset chat history."""
        self.chat_history = []
        logger.info("Conversation history reset")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get current conversation history."""
        return self.chat_history


if __name__ == "__main__":
    # Test the AI brain
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('../../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize AI
    ai = AIBrain(config)
    
    # Test commands
    test_inputs = [
        "Move forward for 3 seconds",
        "Turn left",
        "Go backward for 5 seconds",
        "Stop",
        "What's the weather like today?",
        "Tell me a joke",
    ]
    
    print("\n" + "="*60)
    print("AI BRAIN TEST (NEW GOOGLE-GENAI SDK)")
    print("="*60 + "\n")
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        response, movement = ai.process(user_input)
        print(f"🤖 Robot: {response}")
        if movement:
            print(f"🚗 Movement: {movement}")
        print("-" * 60)