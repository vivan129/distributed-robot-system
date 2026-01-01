"""
AI Brain Module
Natural language processing using Google Gemini
"""

import os
import re
import json
import logging
from google import genai

logger = logging.getLogger(__name__)


class AIBrain:
    def __init__(self, config):
        self.config = config
        
        # Initialize Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("✗ GEMINI_API_KEY not found in environment")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=api_key)
                self.model = config.get('gemini_model', 'gemini-2.0-flash-exp')
                logger.info("✓ Gemini AI connected")
            except Exception as e:
                logger.error(f"✗ Gemini initialization failed: {e}")
                self.client = None
                
    async def process(self, text):
        """
        Process user input and generate response + optional movement command
        
        Args:
            text: User's speech/text input
            
        Returns:
            tuple: (response_text, movement_command_dict or None)
        """
        if not self.client:
            return "AI is offline", None
            
        # First, check for explicit movement commands
        movement = self._parse_movement_command(text)
        
        # Generate AI response
        response = await self._generate_response(text)
        
        # Check if AI response contains movement instructions
        if not movement:
            movement = self._extract_movement_from_response(response)
            
        return response, movement
        
    def _parse_movement_command(self, text):
        """
        Extract movement commands from text
        
        Returns:
            dict or None: {'direction': 'forward', 'duration': 3}
        """
        text = text.lower()
        
        # Pattern: "move forward for 3 seconds"
        match = re.search(r'(forward|backward|left|right|back|front).*?(\d+)\s*second', text)
        if match:
            direction = match.group(1)
            if direction in ['back', 'backward']:
                direction = 'backward'
            elif direction == 'front':
                direction = 'forward'
            return {'direction': direction, 'duration': int(match.group(2))}
        
        # Simple direction commands
        if 'forward' in text or 'front' in text:
            return {'direction': 'forward', 'duration': 2}
        if 'backward' in text or 'back' in text:
            return {'direction': 'backward', 'duration': 2}
        if 'left' in text:
            return {'direction': 'left', 'duration': 1}
        if 'right' in text:
            return {'direction': 'right', 'duration': 1}
        if 'stop' in text:
            return {'direction': 'stop', 'duration': 0}
            
        return None
        
    async def _generate_response(self, text):
        """
        Generate AI response using Gemini
        """
        try:
            prompt = f"""You are a friendly robot assistant. Respond in 1-2 short sentences.
If the user asks you to move, respond naturally but DO NOT include movement instructions in your text.

User: {text}
Robot:"""
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 100
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return "Sorry, I'm having trouble thinking right now."
            
    def _extract_movement_from_response(self, response):
        """
        Extract JSON movement command if AI included it
        """
        try:
            if '{' in response:
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
        except:
            pass
        return None
