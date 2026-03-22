#!/usr/bin/env python3
"""
LoveGuard AI Analysis Engine
Deterministic script for conversation analysis using OpenAI GPT-4
"""

import openai
import json
import os
import time
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        """Initialize the AI analyzer with OpenAI configuration"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4"
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
    def analyze_conversation(
        self, 
        conversation_text: str, 
        include_context: bool = True, 
        detailed: bool = False,
        user_tier: str = "free"
    ) -> Dict:
        """
        Analyze conversation for relationship red flags and safety concerns
        
        Args:
            conversation_text: Raw conversation text to analyze
            include_context: Whether to consider broader relationship context
            detailed: Whether to provide detailed psychological insights
            user_tier: User subscription tier (affects analysis depth)
            
        Returns:
            Dictionary with analysis results
        """
        
        # Input validation
        if not conversation_text or len(conversation_text.strip()) == 0:
            raise ValueError("Conversation text cannot be empty")
            
        # Truncate if too long (GPT-4 token limits)
        max_chars = 4000
        if len(conversation_text) > max_chars:
            conversation_text = conversation_text[:max_chars] + "..."
            logger.warning(f"Conversation truncated to {max_chars} characters")
        
        # Adjust analysis depth based on user tier
        if user_tier == "free":
            detailed = False
            
        # Build system prompt
        system_prompt = self._build_system_prompt(detailed)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(
            conversation_text, 
            include_context, 
            detailed
        )
        
        # Attempt analysis with retries
        for attempt in range(self.max_retries):
            try:
                response = self._call_openai_api(system_prompt, user_prompt)
                result = self._parse_response(response)
                
                # Validate result structure
                self._validate_result(result)
                
                logger.info("AI analysis completed successfully")
                return result
                
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise e
                    
            except openai.APIError as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise e
    
    def _build_system_prompt(self, detailed: bool) -> str:
        """Build the system prompt for AI analysis"""
        base_prompt = """You are a relationship safety expert AI. Analyze conversations for manipulation tactics, 
        emotional abuse patterns, control behaviors, and other relationship red flags.
        
        Provide analysis in this JSON format:
        {
            "risk_score": 0-100,
            "red_flags": ["specific concerning behaviors found"],
            "positive_indicators": ["healthy communication patterns found"], 
            "safety_recommendations": ["specific actionable advice"],
            "crisis_keywords": ["any crisis-indicating phrases found"],
            "explanation": "brief explanation of analysis"
        }
        
        Risk scoring guidelines:
        - 0-30: Healthy communication patterns
        - 31-70: Some concerning behaviors, monitoring recommended
        - 71-100: Serious red flags, immediate attention needed
        
        Look for: gaslighting, isolation attempts, threats, excessive jealousy, control tactics,
        financial abuse, emotional manipulation, love bombing, boundary violations."""
        
        if detailed:
            base_prompt += "\n\nProvide detailed psychological insights and long-term pattern analysis."
        else:
            base_prompt += "\n\nProvide concise, actionable analysis."
            
        return base_prompt
    
    def _build_user_prompt(
        self, 
        conversation_text: str, 
        include_context: bool, 
        detailed: bool
    ) -> str:
        """Build the user prompt with conversation text"""
        
        prompt = f'Analyze this conversation for relationship safety concerns:\n\n"{conversation_text}"\n\n'
        
        if detailed:
            prompt += 'Provide detailed psychological insights and patterns.\n'
        else:
            prompt += 'Provide concise analysis.\n'
            
        if include_context:
            prompt += 'Consider broader relationship context and long-term patterns.\n'
        else:
            prompt += 'Focus only on this specific conversation.\n'
            
        prompt += 'Return only valid JSON.'
        
        return prompt
    
    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Make the actual API call to OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
            timeout=30
        )
        
        return response.choices[0].message.content.strip()
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse the JSON response from OpenAI"""
        # Clean up response text
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
            
        # Parse JSON
        try:
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("Invalid JSON response from AI model")
    
    def _validate_result(self, result: Dict) -> None:
        """Validate the structure of analysis results"""
        required_fields = ['risk_score', 'red_flags', 'positive_indicators', 'safety_recommendations']
        
        for field in required_fields:
            if field not in result:
                result[field] = [] if field != 'risk_score' else 0
                
        # Ensure risk score is in valid range
        if not isinstance(result['risk_score'], (int, float)):
            result['risk_score'] = 0
        else:
            result['risk_score'] = max(0, min(100, int(result['risk_score'])))
            
        # Ensure list fields are lists
        for field in ['red_flags', 'positive_indicators', 'safety_recommendations']:
            if not isinstance(result[field], list):
                result[field] = []

def main():
    """Command line interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ai_analyzer.py 'conversation text'")
        sys.exit(1)
        
    conversation_text = sys.argv[1]
    
    try:
        analyzer = AIAnalyzer()
        result = analyzer.analyze_conversation(conversation_text)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()