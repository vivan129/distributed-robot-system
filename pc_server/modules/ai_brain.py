#!/usr/bin/env python3
"""
AI Brain Module - Google Gemini Integration

Handles natural language processing, conversation management,
and command extraction using Google Gemini AI.

Author: Distributed Robot System
Date: January 2026
"""

import os
import re
import logging
from typing import Dict, Tuple, Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIBrain:
    """Google Gemini-powered AI brain for robot conversation and command processing."""
    
    def __init__(self, config: Dict):
        """
        Initialize AI brain with Gemini.
        
        Args:
            config: AI configuration dictionary
        """
        self.config = config.get('ai', {})
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model_name = self.config.get('model', 'gemini-2.0-flash-exp')
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                'temperature': self.config.get('temperature', 0.7),
                'max_output_tokens': self.config.get('max_tokens', 1024),
            }
        )
        
        # Start chat session
        self.chat = self.model.start_chat(history=[])
        
        # System prompt for robot behavior
        self.system_prompt = self._build_system_prompt()
        
        # Movement command patterns
        self.command_patterns = {
            'forward': r'(?:move|go|drive|walk)\s+forward',
            'backward': r'(?:move|go|drive|walk|back)\s+(?:backward|back)',
            'left': r'turn\s+left',
            'right': r'turn\s+right',
            'stop': r'stop|halt|freeze',
        }
        
        logger.info(f"AI Brain initialized with {self.model_name}")
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for robot behavior."""
        return """You are a friendly, helpful robot assistant. You can:
1. Have natural conversations with humans
2. Execute movement commands (forward, backward, left, right, stop)
3. Respond with personality and humor
4. Extract time durations from commands (e.g., "for 3 seconds")

When you receive a movement command:
- Acknowledge it naturally
- If a duration is specified, remember it
- Be encouraging and friendly

When having conversations:
- Be concise (2-3 sentences max)
- Show personality
- Be helpful and informative

Remember: You are a physical robot, so relate your responses to movement and the real world.
"""
    
    def process(self, user_input: str) -> Tuple[str, Optional[Dict]]:
        """
        Process user input and extract commands.
        
        Args:
            user_input: User's speech or text input
        
        Returns:
            Tuple of (AI response text, movement command dict or None)
        """
        try:
            # Check for movement commands
            movement_cmd = self._extract_movement_command(user_input)
            
            # Generate AI response
            prompt = f"{self.system_prompt}\n\nUser: {user_input}\nRobot:"
            response = self.chat.send_message(prompt)
            ai_text = response.text.strip()
            
            logger.info(f"User: {user_input}")
            logger.info(f"AI: {ai_text}")
            
            if movement_cmd:
                logger.info(f"Command: {movement_cmd}")
            
            return ai_text, movement_cmd
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return "Sorry, I had trouble processing that. Could you try again?", None
    
    def _extract_movement_command(self, text: str) -> Optional[Dict]:
        """
        Extract movement commands from text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Movement command dict or None
        """
        text_lower = text.lower()
        
        # Check each command pattern
        for direction, pattern in self.command_patterns.items():
            if re.search(pattern, text_lower):
                # Extract duration if specified
                duration = self._extract_duration(text_lower)
                
                return {
                    'direction': direction,
                    'duration': duration if duration else 2.0,  # Default 2 seconds
                    'speed': 75  # Default speed
                }
        
        return None
    
    def _extract_duration(self, text: str) -> Optional[float]:
        """
        Extract time duration from text.
        
        Args:
            text: Input text
        
        Returns:
            Duration in seconds or None
        """
        # Patterns for duration extraction
        patterns = [
            r'for\s+(\d+(?:\.\d+)?)\s+seconds?',
            r'(\d+(?:\.\d+)?)\s+seconds?',
            r'for\s+(\d+(?:\.\d+)?)\s+sec',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def reset_conversation(self):
        """Reset chat history."""
        self.chat = self.model.start_chat(history=[])
        logger.info("Conversation history reset")
    
    def get_conversation_history(self) -> list:
        """Get current conversation history."""
        return self.chat.history


if __name__ == "__main__":
    # Test the AI brain
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('../config/robot_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    brain = AIBrain(config)
    
    # Test conversations
    test_inputs = [
        "Move forward for 3 seconds",
        "Turn left",
        "Tell me a joke",
        "Go backward for 5 seconds",
        "Stop",
        "What's the weather like?"
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        response, command = brain.process(user_input)
        print(f"User: {user_input}")
        print(f"AI: {response}")
        if command:
            print(f"Command: {command}")
