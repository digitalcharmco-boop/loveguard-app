#!/usr/bin/env python3
"""
LoveGuard Crisis Detection Engine
Deterministic script for detecting crisis situations and providing safety resources
"""

import re
import logging
from typing import Dict, List, Tuple
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrisisDetector:
    def __init__(self):
        """Initialize crisis detection with keyword patterns"""
        self.crisis_keywords = {
            'immediate': [
                'kill myself', 'suicide', 'end my life', 'hurt myself', 'die tonight',
                'going to die', 'overdose', 'jump off', 'hang myself', 'slit my wrists',
                'gun to my head', 'pills', 'can\'t go on', 'better off dead',
                'end it all', 'no way out', 'final goodbye', 'goodbye forever'
            ],
            'violence': [
                'i\'ll kill you', 'you\'re dead', 'i have a gun', 'i have a knife',
                'i\'ll hurt you', 'you better watch out', 'i know where you live',
                'i\'ll find you', 'you can\'t hide', 'i\'ll make you pay',
                'nobody will find you', 'disappear forever', 'teach you a lesson'
            ],
            'physical_abuse': [
                'hit you', 'punch you', 'slap you', 'beat you', 'hurt you',
                'black eye', 'bruises', 'broken', 'hospital', 'stitches',
                'push you down', 'throw you', 'choke you', 'strangle',
                'grab you', 'shake you', 'slam you'
            ],
            'stalking': [
                'i know where you are', 'i\'m watching you', 'i followed you',
                'i saw you with', 'i know who you were with', 'i tracked your phone',
                'i checked your location', 'i\'m outside your', 'i drove by',
                'i know your schedule', 'i\'m always watching', 'you can\'t hide from me'
            ],
            'control': [
                'you can\'t leave', 'you belong to me', 'you\'re mine', 'you owe me',
                'you\'re not allowed', 'i forbid you', 'you must', 'you will',
                'give me your password', 'prove it to me', 'you\'re lying',
                'i don\'t believe you', 'show me your phone'
            ]
        }
        
        self.safety_resources = {
            'immediate': [
                "🆘 CALL 911 IMMEDIATELY if you are in immediate danger",
                "National Suicide Prevention Lifeline: 988 (24/7)",
                "Crisis Text Line: Text HOME to 741741", 
                "National Domestic Violence Hotline: 1-800-799-7233",
                "If safe to do so, go to your nearest hospital emergency room"
            ],
            'high': [
                "Consider calling 911 if you feel unsafe",
                "Create a safety plan immediately",
                "Reach out to trusted friends or family",
                "Contact a local domestic violence shelter",
                "Document any threats or concerning behavior"
            ],
            'moderate': [
                "Consider speaking with a counselor or therapist",
                "Confide in trusted friends or family members", 
                "Start documenting concerning behaviors",
                "Learn about healthy relationship patterns",
                "Create a support network"
            ],
            'low': [
                "Continue monitoring communication patterns",
                "Trust your instincts about the relationship",
                "Maintain connections with friends and family",
                "Learn about healthy relationship boundaries"
            ]
        }
        
        # Base safety resources for all levels
        self.base_resources = [
            "National Domestic Violence Hotline: 1-800-799-7233 (24/7, free, confidential)",
            "Crisis Text Line: Text HOME to 741741",
            "National Sexual Assault Hotline: 1-800-656-4673",
            "National Human Trafficking Hotline: 1-888-373-7888"
        ]
    
    def assess_crisis_level(
        self, 
        conversation_text: str, 
        analysis_result: Dict = None
    ) -> Tuple[str, List[str], Dict]:
        """
        Assess the crisis level based on conversation content and AI analysis
        
        Args:
            conversation_text: Raw conversation text
            analysis_result: Optional AI analysis results
            
        Returns:
            Tuple of (crisis_level, safety_resources, crisis_details)
        """
        
        if not conversation_text:
            return 'low', self.base_resources, {}
            
        text_lower = conversation_text.lower()
        
        # Check for crisis indicators
        crisis_matches = self._find_crisis_matches(text_lower)
        
        # Determine crisis level
        crisis_level = self._calculate_crisis_level(crisis_matches, analysis_result)
        
        # Get appropriate resources
        safety_resources = self._get_safety_resources(crisis_level)
        
        # Create crisis details
        crisis_details = {
            'crisis_level': crisis_level,
            'matches_found': crisis_matches,
            'immediate_action_required': crisis_level == 'immediate',
            'safety_plan_needed': crisis_level in ['immediate', 'high']
        }
        
        logger.info(f"Crisis assessment completed: {crisis_level} level")
        return crisis_level, safety_resources, crisis_details
    
    def _find_crisis_matches(self, text_lower: str) -> Dict[str, List[str]]:
        """Find all crisis keyword matches in text"""
        matches = {}
        
        for category, keywords in self.crisis_keywords.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                matches[category] = found_keywords
                
        return matches
    
    def _calculate_crisis_level(
        self, 
        crisis_matches: Dict[str, List[str]], 
        analysis_result: Dict = None
    ) -> str:
        """Calculate overall crisis level based on matches and AI analysis"""
        
        # Check for immediate crisis indicators
        if 'immediate' in crisis_matches:
            return 'immediate'
            
        # Check AI analysis risk score if available
        if analysis_result and 'risk_score' in analysis_result:
            risk_score = analysis_result['risk_score']
            if risk_score >= 90:
                return 'immediate'
            elif risk_score >= 75:
                return 'high'
                
        # Check for high-risk categories
        high_risk_categories = ['violence', 'physical_abuse']
        for category in high_risk_categories:
            if category in crisis_matches:
                return 'high'
                
        # Check for moderate-risk indicators
        moderate_risk_categories = ['stalking', 'control']
        for category in moderate_risk_categories:
            if category in crisis_matches:
                return 'moderate'
                
        # Check AI analysis for moderate risk
        if analysis_result and 'risk_score' in analysis_result:
            risk_score = analysis_result['risk_score']
            if risk_score >= 40:
                return 'moderate'
                
        return 'low'
    
    def _get_safety_resources(self, crisis_level: str) -> List[str]:
        """Get appropriate safety resources for crisis level"""
        resources = self.safety_resources.get(crisis_level, [])
        resources.extend(self.base_resources)
        return resources
    
    def generate_safety_plan(self, crisis_level: str) -> List[str]:
        """Generate a personalized safety plan based on crisis level"""
        
        if crisis_level in ['immediate', 'high']:
            return [
                "Identify safe places you can go (friends, family, shelters)",
                "Keep important documents in a safe, accessible place",
                "Have a bag packed with essentials",
                "Identify trusted people you can call for help",
                "Plan safe times to leave (when abuser is not present)",
                "Memorize important phone numbers",
                "Have a code word with friends/family to signal you need help",
                "Keep some money in a safe place",
                "Plan the safest route out of your home",
                "Consider staying with trusted friends/family temporarily"
            ]
        elif crisis_level == 'moderate':
            return [
                "Identify people you trust and can talk to",
                "Keep important phone numbers accessible",
                "Pay attention to warning signs of escalation",
                "Document concerning incidents with dates/times",
                "Maintain financial independence when possible",
                "Stay connected with friends and family",
                "Consider counseling or support groups",
                "Learn about healthy relationship patterns"
            ]
        else:
            return [
                "Continue building healthy communication skills",
                "Maintain strong friendships and family relationships",
                "Set and maintain personal boundaries",
                "Stay aware of relationship warning signs",
                "Practice self-care and maintain independence"
            ]
    
    def check_stalking_behaviors(self, conversation_text: str) -> List[str]:
        """Check for specific stalking behavior indicators"""
        
        if not conversation_text:
            return []
            
        text_lower = conversation_text.lower()
        found_behaviors = []
        
        stalking_patterns = [
            (r'i know where you (are|live|work|go)', 'Location tracking/surveillance'),
            (r'i (saw|watched|followed) you', 'Physical surveillance'),
            (r'i (checked|tracked) your (phone|location|car)', 'Digital stalking'),
            (r'i\'m (outside|near|at) your', 'Physical proximity threats'),
            (r'i know (who|what|when) you', 'Excessive monitoring')
        ]
        
        for pattern, description in stalking_patterns:
            if re.search(pattern, text_lower):
                found_behaviors.append(description)
                
        return found_behaviors
    
    def check_financial_abuse(self, conversation_text: str) -> List[str]:
        """Check for financial abuse indicators"""
        
        if not conversation_text:
            return []
            
        text_lower = conversation_text.lower()
        found_indicators = []
        
        financial_patterns = [
            (r'(give me|hand over) your (money|paycheck|card)', 'Financial control'),
            (r'you (can\'t|aren\'t allowed to) (spend|buy|work)', 'Economic restriction'),
            (r'(quit your job|stop working)', 'Employment interference'), 
            (r'you owe me', 'Debt manipulation'),
            (r'i control the (money|finances|accounts)', 'Financial dominance')
        ]
        
        for pattern, description in financial_patterns:
            if re.search(pattern, text_lower):
                found_indicators.append(description)
                
        return found_indicators

def main():
    """Command line interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python crisis_detector.py 'conversation text'")
        sys.exit(1)
        
    conversation_text = sys.argv[1]
    
    try:
        detector = CrisisDetector()
        crisis_level, resources, details = detector.assess_crisis_level(conversation_text)
        
        result = {
            'crisis_level': crisis_level,
            'safety_resources': resources,
            'crisis_details': details,
            'stalking_behaviors': detector.check_stalking_behaviors(conversation_text),
            'financial_abuse': detector.check_financial_abuse(conversation_text),
            'safety_plan': detector.generate_safety_plan(crisis_level)
        }
        
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()