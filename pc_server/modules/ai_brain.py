#!/usr/bin/env python3
"""
AI Brain Module - Google Gemini Integration
Handles natural language processing and command interpretation
"""

import os
import re
import logging
from typing import Dict, Tuple, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AIBrain:
    """Google Gemini AI integration for natural language processing."""
    
    def __init__(self, config: Dict):
        """Initialize AI Brain with Gemini API.
        
        Args:
            config: Configuration dictionary from robot_config.yaml
        """
        self.config = config
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=config.get('ai', {}).get('model', 'gemini-2.0-flash-exp')
        )
        
        # System prompt for robot personality
        self.system_prompt = """
You are a friendly, helpful robot assistant. You can:
1. Move around (forward, backward, left, right)
2. Answer questions
3. Have conversations

When user gives movement commands, respond naturally but include the command in your response.

Example commands:
- "Move forward" → Extract: {"direction": "forward", "duration": 2}
- "Go backward for 5 seconds" → Extract: {"direction": "backward", "duration": 5}
- "Turn left" → Extract: {"direction": "left", "duration": 1.5}
- "Stop" → Extract: {"direction": "stop", "duration": 0}

For regular conversations, just respond naturally without movement commands.
Keep responses brief (2-3 sentences max).
"""
        
        logger.info(f"AI Brain initialized with model: {self.model.model_name}")
    
    def process(self, user_input: str) -> Tuple[str, Optional[Dict]]:
        """Process user input and return response + movement command.
        
        Args:
            user_input: User's speech text
        
        Returns:
            Tuple of (response_text, movement_command_dict or None)
        """
        try:
            # First, try to extract movement command
            movement_cmd = self._extract_movement_command(user_input)
            
            # Generate AI response
            prompt = f"{self.system_prompt}\n\nUser: {user_input}\nRobot:"
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.config.get('ai', {}).get('temperature', 0.7),
                    max_output_tokens=self.config.get('ai', {}).get('max_tokens', 1000)
                )
            )
            
            response_text = response.text.strip()
            
            logger.info(f"User: {user_input}")
            logger.info(f"Robot: {response_text}")
            if movement_cmd:
                logger.info(f"Movement: {movement_cmd}")
            
            return response_text, movement_cmd
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            fallback = self.config.get('ai', {}).get('fallback_responses', [
                "I didn't quite understand that."
            ])[0]
            return fallback, None
    
    def _extract_movement_command(self, text: str) -> Optional[Dict]:
        """Extract movement command from text using pattern matching.
        
        Args:
            text: User input text
        
        Returns:
            Movement command dict or None
        """
        text = text.lower()
        
        # Patterns for movement commands
        patterns = [
            (r'stop', {'direction': 'stop', 'duration': 0}),
            (r'move forward|go forward|go ahead|move ahead', {'direction': 'forward', 'duration': 2}),
            (r'move back|go back|reverse|move backward|go backward', {'direction': 'backward', 'duration': 2}),
            (r'turn left|go left|left turn', {'direction': 'left', 'duration': 1.5}),
            (r'turn right|go right|right turn', {'direction': 'right', 'duration': 1.5}),
        ]
        
        for pattern, cmd in patterns:
            if re.search(pattern, text):
                # Try to extract duration
                duration_match = re.search(r'(\d+)\s*(?:second|sec)', text)
                if duration_match:
                    cmd['duration'] = int(duration_match.group(1))
                return cmd
        
        return None
    
    def chat(self, message: str) -> str:
        """Simple chat without movement commands.
        
        Args:
            message: User message
        
        Returns:
            AI response text
        """
        response, _ = self.process(message)
        return response


if __name__ == "__main__":
    # Test the AI Brain
    import yaml
    
    logging.basicConfig(level=logging.INFO)
    
    with open('config/robot_config.yaml') as f:
        config = yaml.safe_load(f)
    
    brain = AIBrain(config)
    
    # Test commands
    test_inputs = [
        "Move forward for 3 seconds",
        "Turn left",
        "What's your name?",
        "Tell me a joke",
        "Go backward for 5 seconds",
        "Stop"
    ]
    
    for text in test_inputs:
        print(f"\n{'='*50}")
        response, cmd = brain.process(text)
        print(f"Input: {text}")
        print(f"Response: {response}")
        print(f"Command: {cmd}")
