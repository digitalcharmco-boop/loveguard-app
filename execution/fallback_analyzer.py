#!/usr/bin/env python3
"""
LoveGuard Fallback Analyzer
Deterministic keyword-based analysis when AI services are unavailable
"""

import re
import logging
from typing import Dict, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FallbackAnalyzer:
    def __init__(self):
        """Initialize fallback analyzer with keyword patterns"""
        
        # Crisis and suicide keywords (highest weight)
        self.crisis_keywords = [
            'kill myself', 'suicide', 'end my life', 'hurt myself', 'die tonight',
            'going to die', 'overdose', 'jump off', 'hang myself', 'slit my wrists',
            'gun to my head', 'pills', 'can\'t go on', 'better off dead',
            'end it all', 'no way out', 'final goodbye'
        ]
        
        # Abuse and threat keywords (high weight)
        self.abuse_keywords = [
            'you\'re worthless', 'nobody will love you', 'you\'re crazy', 'you\'re stupid',
            'shut up', 'i\'ll kill you', 'you better', 'or else', 'you owe me',
            'you belong to me', 'you can\'t leave', 'i\'ll find you', 'track your phone',
            'isolate', 'your friends hate you', 'your family', 'embarrass you',
            'i\'ll hurt you', 'you\'re dead', 'i have a weapon', 'teach you a lesson'
        ]
        
        # Control and manipulation keywords (medium weight)
        self.control_keywords = [
            'you can\'t', 'you\'re not allowed', 'i forbid', 'you must', 'you will',
            'give me your password', 'where are you', 'who are you with', 'prove it',
            'send me a photo', 'you\'re lying', 'i don\'t believe you', 'check in with me',
            'ask permission', 'you need to', 'i decide', 'my rules'
        ]
        
        # Gaslighting patterns (medium weight)
        self.gaslighting_keywords = [
            'you\'re imagining things', 'that never happened', 'you\'re being dramatic',
            'you\'re too sensitive', 'you\'re overreacting', 'you\'re paranoid',
            'you remember wrong', 'i never said that', 'you\'re making it up',
            'you\'re being crazy', 'that\'s not what happened'
        ]
        
        # Financial abuse keywords (medium weight)
        self.financial_keywords = [
            'give me your money', 'you can\'t spend', 'i control the money',
            'quit your job', 'you can\'t work', 'give me your paycheck',
            'you\'re not allowed to buy', 'i\'ll take your card', 'you owe me money'
        ]
        
        # Positive communication keywords (negative weight - reduces risk)
        self.positive_keywords = [
            'i love you', 'i respect', 'i support', 'your choice', 'what do you think',
            'i\'m sorry', 'you\'re right', 'i understand', 'thank you', 'please',
            'how are you feeling', 'i\'m here for you', 'i appreciate you',
            'your opinion matters', 'i trust you', 'you decide'
        ]
        
        # Weight values for scoring
        self.weights = {
            'crisis': 40,      # Each crisis keyword adds 40 points
            'abuse': 25,       # Each abuse keyword adds 25 points  
            'control': 15,     # Each control keyword adds 15 points
            'gaslighting': 20, # Each gaslighting keyword adds 20 points
            'financial': 15,   # Each financial abuse keyword adds 15 points
            'positive': -8     # Each positive keyword subtracts 8 points
        }
    
    def analyze_conversation(
        self,
        conversation_text: str,
        include_context: bool = True,
        detailed: bool = False,
        user_tier: str = "free"
    ) -> Dict:
        """
        Analyze conversation using keyword-based detection
        
        Args:
            conversation_text: Raw conversation text to analyze
            include_context: Whether to consider broader patterns (affects scoring)
            detailed: Whether to provide detailed explanations
            user_tier: User subscription tier
            
        Returns:
            Dictionary with analysis results matching AI analyzer format
        """
        
        if not conversation_text or len(conversation_text.strip()) == 0:
            raise ValueError("Conversation text cannot be empty")
        
        text_lower = conversation_text.lower()
        
        # Find keyword matches
        matches = self._find_keyword_matches(text_lower)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(matches, include_context)
        
        # Generate findings
        red_flags = self._generate_red_flags(matches, detailed)
        positive_indicators = self._generate_positive_indicators(matches, detailed)
        safety_recommendations = self._generate_safety_recommendations(risk_score, matches)
        
        # Create explanation
        explanation = self._generate_explanation(matches, risk_score, detailed)
        
        result = {
            'risk_score': risk_score,
            'red_flags': red_flags,
            'positive_indicators': positive_indicators,
            'safety_recommendations': safety_recommendations,
            'crisis_keywords': matches.get('crisis', []),
            'explanation': explanation,
            'analysis_method': 'fallback',
            'keyword_matches': matches if detailed else {}
        }
        
        logger.info(f"Fallback analysis completed: risk score {risk_score}")
        return result
    
    def _find_keyword_matches(self, text_lower: str) -> Dict[str, List[str]]:
        """Find all keyword matches in the text"""
        
        matches = {
            'crisis': [],
            'abuse': [], 
            'control': [],
            'gaslighting': [],
            'financial': [],
            'positive': []
        }
        
        # Check each category
        keyword_sets = {
            'crisis': self.crisis_keywords,
            'abuse': self.abuse_keywords,
            'control': self.control_keywords, 
            'gaslighting': self.gaslighting_keywords,
            'financial': self.financial_keywords,
            'positive': self.positive_keywords
        }
        
        for category, keywords in keyword_sets.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches[category].append(keyword)
        
        return matches
    
    def _calculate_risk_score(self, matches: Dict[str, List[str]], include_context: bool) -> int:
        """Calculate risk score based on keyword matches"""
        
        total_score = 0
        
        # Add scores for each category
        for category, keywords in matches.items():
            if category in self.weights:
                category_score = len(keywords) * self.weights[category]
                total_score += category_score
        
        # Context modifier - if considering broader context, slightly increase negative indicators
        if include_context:
            negative_indicators = len(matches['abuse']) + len(matches['control']) + len(matches['gaslighting'])
            if negative_indicators > 2:
                total_score += 10  # Pattern bonus
        
        # Ensure score is in valid range
        risk_score = max(0, min(100, total_score))
        
        return risk_score
    
    def _generate_red_flags(self, matches: Dict[str, List[str]], detailed: bool) -> List[str]:
        """Generate red flag descriptions based on matches"""
        
        red_flags = []
        
        if matches['crisis']:
            red_flags.append("Crisis language or self-harm indicators detected")
            if detailed:
                red_flags.append(f"Specific crisis terms: {', '.join(matches['crisis'][:3])}")
        
        if matches['abuse']:
            red_flags.append("Abusive language and threatening behavior identified")
            if detailed:
                red_flags.append(f"Abuse patterns: {len(matches['abuse'])} threatening phrases found")
        
        if matches['control']:
            red_flags.append("Controlling behavior and restriction patterns found")
            if detailed:
                red_flags.append(f"Control tactics: {len(matches['control'])} controlling phrases detected")
        
        if matches['gaslighting']:
            red_flags.append("Gaslighting and reality manipulation tactics identified")
            if detailed:
                red_flags.append(f"Gaslighting patterns: {len(matches['gaslighting'])} manipulative phrases")
        
        if matches['financial']:
            red_flags.append("Financial control and economic abuse indicators present")
            if detailed:
                red_flags.append(f"Financial abuse: {len(matches['financial'])} economic control phrases")
        
        # Pattern-based red flags
        total_negative = sum(len(matches[cat]) for cat in ['abuse', 'control', 'gaslighting', 'financial'])
        if total_negative >= 5:
            red_flags.append("Multiple manipulation tactics detected in single conversation")
        
        return red_flags
    
    def _generate_positive_indicators(self, matches: Dict[str, List[str]], detailed: bool) -> List[str]:
        """Generate positive indicator descriptions"""
        
        positive_indicators = []
        
        positive_count = len(matches['positive'])
        
        if positive_count >= 3:
            positive_indicators.append("Multiple positive communication patterns present")
            if detailed:
                positive_indicators.append(f"Healthy communication: {positive_count} supportive phrases found")
        elif positive_count >= 1:
            positive_indicators.append("Some positive communication elements identified")
        
        # Check for absence of major red flags
        major_concerns = len(matches['crisis']) + len(matches['abuse'])
        if major_concerns == 0:
            positive_indicators.append("No immediate crisis or abuse language detected")
        
        return positive_indicators
    
    def _generate_safety_recommendations(self, risk_score: int, matches: Dict[str, List[str]]) -> List[str]:
        """Generate safety recommendations based on risk score and patterns"""
        
        recommendations = []
        
        # Crisis-specific recommendations
        if matches['crisis']:
            recommendations.extend([
                "Seek immediate help from crisis hotlines or emergency services",
                "Reach out to trusted friends, family, or mental health professionals",
                "Contact National Suicide Prevention Lifeline: 988"
            ])
        
        # High risk recommendations
        elif risk_score >= 70:
            recommendations.extend([
                "Consider reaching out to domestic violence support services",
                "Document concerning conversations and incidents",
                "Create a safety plan with trusted contacts",
                "Consider speaking with a counselor or therapist"
            ])
        
        # Moderate risk recommendations  
        elif risk_score >= 40:
            recommendations.extend([
                "Monitor communication patterns for escalation",
                "Consider discussing concerns with trusted friends or family",
                "Learn about healthy relationship communication patterns",
                "Consider couples counseling or individual therapy"
            ])
        
        # Low risk recommendations
        else:
            recommendations.extend([
                "Continue monitoring communication patterns",
                "Maintain healthy boundaries in the relationship",
                "Stay connected with friends and family support network"
            ])
        
        # Always include basic safety resources
        recommendations.append("Trust your instincts about safety and relationship concerns")
        
        return recommendations
    
    def _generate_explanation(self, matches: Dict[str, List[str]], risk_score: int, detailed: bool) -> str:
        """Generate explanation of the analysis"""
        
        total_concerns = sum(len(matches[cat]) for cat in ['crisis', 'abuse', 'control', 'gaslighting', 'financial'])
        total_positive = len(matches['positive'])
        
        if detailed:
            explanation = f"Keyword-based analysis identified {total_concerns} concerning indicators and {total_positive} positive communication elements. "
        else:
            explanation = "Analysis completed using keyword-based detection. "
        
        if matches['crisis']:
            explanation += "Crisis language detected requiring immediate attention. "
        elif risk_score >= 70:
            explanation += "Multiple serious relationship concerns identified. "
        elif risk_score >= 40:
            explanation += "Some concerning communication patterns found. "
        else:
            explanation += "No major relationship red flags detected. "
        
        if not detailed:
            explanation += "(AI analysis temporarily unavailable - using backup detection system)"
        
        return explanation

def main():
    """Command line interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fallback_analyzer.py 'conversation text'")
        sys.exit(1)
    
    conversation_text = sys.argv[1]
    
    try:
        analyzer = FallbackAnalyzer()
        result = analyzer.analyze_conversation(conversation_text, detailed=True)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()