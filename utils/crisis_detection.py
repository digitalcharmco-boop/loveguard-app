from typing import Dict, List

def assess_crisis_level(conversation_text: str, analysis_result: Dict) -> str:
    """
    Assess the crisis level based on conversation content and AI analysis
    Returns: 'immediate', 'high', 'moderate', 'low'
    """
    
    # Immediate crisis keywords
    immediate_crisis_keywords = [
        'kill myself', 'suicide', 'end my life', 'hurt myself', 'die tonight',
        'going to die', 'overdose', 'jump off', 'hang myself', 'slit my wrists',
        'gun to my head', 'pills', 'can\'t go on', 'better off dead'
    ]
    
    # High risk keywords
    high_risk_keywords = [
        'i\'ll kill you', 'you\'re dead', 'i have a gun', 'i have a knife',
        'i\'ll hurt you', 'you better watch out', 'i know where you live',
        'i\'ll find you', 'you can\'t hide', 'i\'ll make you pay',
        'nobody will find you', 'disappear forever'
    ]
    
    # Physical abuse indicators
    physical_abuse_keywords = [
        'hit you', 'punch you', 'slap you', 'beat you', 'hurt you',
        'black eye', 'bruises', 'broken', 'hospital', 'stitches',
        'push you down', 'throw you', 'choke you', 'strangle'
    ]
    
    text_lower = conversation_text.lower()
    
    # Check for immediate crisis
    immediate_matches = [kw for kw in immediate_crisis_keywords if kw in text_lower]
    if immediate_matches or analysis_result.get('risk_score', 0) >= 90:
        return 'immediate'
    
    # Check for high risk
    high_risk_matches = [kw for kw in high_risk_keywords if kw in text_lower]
    physical_abuse_matches = [kw for kw in physical_abuse_keywords if kw in text_lower]
    
    if (high_risk_matches or physical_abuse_matches or 
        analysis_result.get('risk_score', 0) >= 75):
        return 'high'
    
    # Check for moderate risk
    if analysis_result.get('risk_score', 0) >= 40:
        return 'moderate'
    
    return 'low'

def get_safety_resources(crisis_level: str) -> List[str]:
    """
    Get appropriate safety resources based on crisis level
    """
    
    base_resources = [
        "National Domestic Violence Hotline: 1-800-799-7233 (24/7, free, confidential)",
        "Crisis Text Line: Text HOME to 741741",
        "National Sexual Assault Hotline: 1-800-656-4673"
    ]
    
    if crisis_level == 'immediate':
        return [
            "🆘 CALL 911 IMMEDIATELY if you are in immediate danger",
            "National Suicide Prevention Lifeline: 988 (24/7)",
            "Crisis Text Line: Text HOME to 741741",
            "National Domestic Violence Hotline: 1-800-799-7233",
            "If safe to do so, go to your nearest hospital emergency room"
        ] + base_resources
    
    elif crisis_level == 'high':
        return [
            "Consider calling 911 if you feel unsafe",
            "Create a safety plan immediately",
            "Reach out to trusted friends or family",
            "Contact a local domestic violence shelter",
            "Document any threats or concerning behavior"
        ] + base_resources
    
    elif crisis_level == 'moderate':
        return [
            "Consider speaking with a counselor or therapist",
            "Confide in trusted friends or family members",
            "Start documenting concerning behaviors",
            "Learn about healthy relationship patterns",
            "Create a support network"
        ] + base_resources
    
    else:  # low
        return [
            "Continue monitoring communication patterns",
            "Trust your instincts about the relationship",
            "Maintain connections with friends and family",
            "Learn about healthy relationship boundaries"
        ] + base_resources

def generate_safety_plan(crisis_level: str) -> List[str]:
    """
    Generate a personalized safety plan based on crisis level
    """
    
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
    
    else:  # low
        return [
            "Continue building healthy communication skills",
            "Maintain strong friendships and family relationships",
            "Set and maintain personal boundaries",
            "Stay aware of relationship warning signs",
            "Practice self-care and maintain independence"
        ]

def get_local_resources(location: str = None) -> Dict[str, str]:
    """
    Get local resources (placeholder - in production would use location API)
    """
    
    return {
        "National Resources": {
            "National Domestic Violence Hotline": "1-800-799-7233",
            "Crisis Text Line": "Text HOME to 741741",
            "National Suicide Prevention Lifeline": "988",
            "National Sexual Assault Hotline": "1-800-656-4673",
            "National Human Trafficking Hotline": "1-888-373-7888"
        },
        "Emergency": {
            "Emergency Services": "911",
            "Poison Control": "1-800-222-1222"
        },
        "Online Resources": {
            "National Domestic Violence Hotline": "https://www.thehotline.org/",
            "Crisis Text Line": "https://www.crisistextline.org/",
            "RAINN": "https://www.rainn.org/",
            "Mental Health America": "https://www.mhanational.org/"
        }
    }

def check_for_stalking_behaviors(conversation_text: str) -> List[str]:
    """
    Check for stalking behavior indicators
    """
    
    stalking_keywords = [
        'i know where you are', 'i\'m watching you', 'i followed you',
        'i saw you with', 'i know who you were with', 'i tracked your phone',
        'i checked your location', 'i\'m outside your', 'i drove by',
        'i know your schedule', 'i\'m always watching', 'you can\'t hide'
    ]
    
    text_lower = conversation_text.lower()
    found_behaviors = []
    
    for keyword in stalking_keywords:
        if keyword in text_lower:
            found_behaviors.append(f"Potential stalking behavior: '{keyword}' detected")
    
    return found_behaviors

def assess_financial_abuse(conversation_text: str) -> List[str]:
    """
    Check for financial abuse indicators
    """
    
    financial_abuse_keywords = [
        'give me your money', 'you can\'t spend', 'i control the money',
        'you don\'t need money', 'quit your job', 'you can\'t work',
        'give me your paycheck', 'you owe me', 'pay me back',
        'i\'ll take your card', 'you\'re not allowed to buy'
    ]
    
    text_lower = conversation_text.lower()
    found_indicators = []
    
    for keyword in financial_abuse_keywords:
        if keyword in text_lower:
            found_indicators.append(f"Financial abuse indicator: '{keyword}' detected")
    
    return found_indicators