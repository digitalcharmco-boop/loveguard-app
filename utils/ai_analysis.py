import openai
import json
import os
from typing import Dict, List

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def analyze_conversation(conversation_text: str, include_context: bool = True, detailed: bool = False) -> Dict:
    """
    Analyze conversation for relationship red flags and safety concerns
    """
    
    # System prompt for AI analysis
    system_prompt = """You are a relationship safety expert AI. Analyze conversations for manipulation tactics, 
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
    
    # User prompt with conversation
    user_prompt = f"""Analyze this conversation for relationship safety concerns:

    "{conversation_text}"
    
    {'Provide detailed psychological insights and patterns.' if detailed else 'Provide concise analysis.'}
    {'Consider broader relationship context and long-term patterns.' if include_context else 'Focus only on this specific conversation.'}
    
    Return only valid JSON."""
    
    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        # Parse response
        analysis_text = response.choices[0].message.content.strip()
        
        # Clean and parse JSON
        if analysis_text.startswith('```json'):
            analysis_text = analysis_text[7:-3]
        elif analysis_text.startswith('```'):
            analysis_text = analysis_text[3:-3]
            
        analysis_result = json.loads(analysis_text)
        
        # Validate required fields
        required_fields = ['risk_score', 'red_flags', 'positive_indicators', 'safety_recommendations']
        for field in required_fields:
            if field not in analysis_result:
                analysis_result[field] = [] if field != 'risk_score' else 0
        
        # Ensure risk score is in valid range
        analysis_result['risk_score'] = max(0, min(100, analysis_result['risk_score']))
        
        return analysis_result
        
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return get_fallback_analysis(conversation_text)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return get_fallback_analysis(conversation_text)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return get_fallback_analysis(conversation_text)

def get_fallback_analysis(conversation_text: str) -> Dict:
    """
    Fallback analysis when AI service is unavailable
    Uses keyword-based detection for basic safety assessment
    """
    
    # Crisis and abuse keywords
    crisis_keywords = [
        'kill', 'suicide', 'hurt myself', 'end it all', 'die', 'weapon',
        'gun', 'knife', 'pills', 'overdose', 'hang myself'
    ]
    
    abuse_keywords = [
        'you\'re worthless', 'nobody will love you', 'you\'re crazy', 'you\'re stupid',
        'shut up', 'i\'ll kill you', 'you better', 'or else', 'you owe me',
        'you belong to me', 'you can\'t leave', 'i\'ll find you', 'track your phone',
        'isolate', 'your friends hate you', 'your family', 'embarrass you'
    ]
    
    control_keywords = [
        'you can\'t', 'you\'re not allowed', 'i forbid', 'you must', 'you will',
        'give me your password', 'where are you', 'who are you with', 'prove it',
        'send me a photo', 'you\'re lying', 'i don\'t believe you'
    ]
    
    positive_keywords = [
        'i love you', 'i respect', 'i support', 'your choice', 'what do you think',
        'i\'m sorry', 'you\'re right', 'i understand', 'thank you', 'please',
        'how are you feeling', 'i\'m here for you'
    ]
    
    text_lower = conversation_text.lower()
    
    # Count keyword matches
    crisis_count = sum(1 for keyword in crisis_keywords if keyword in text_lower)
    abuse_count = sum(1 for keyword in abuse_keywords if keyword in text_lower)
    control_count = sum(1 for keyword in control_keywords if keyword in text_lower)
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    
    # Calculate risk score
    negative_score = (crisis_count * 30) + (abuse_count * 20) + (control_count * 15)
    positive_score = positive_count * 5
    risk_score = max(0, min(100, negative_score - positive_score))
    
    # Generate findings
    red_flags = []
    if crisis_count > 0:
        red_flags.append("Crisis language detected in conversation")
    if abuse_count > 0:
        red_flags.append("Abusive language patterns identified")
    if control_count > 0:
        red_flags.append("Controlling behavior indicators found")
    
    positive_indicators = []
    if positive_count > 2:
        positive_indicators.append("Some positive communication patterns present")
    
    safety_recommendations = []
    if risk_score > 70:
        safety_recommendations.append("Consider reaching out to a domestic violence hotline")
        safety_recommendations.append("Document concerning conversations")
        safety_recommendations.append("Create a safety plan")
    elif risk_score > 30:
        safety_recommendations.append("Monitor communication patterns")
        safety_recommendations.append("Consider talking to a trusted friend or counselor")
    else:
        safety_recommendations.append("Continue monitoring for any changes in communication")
    
    return {
        'risk_score': risk_score,
        'red_flags': red_flags,
        'positive_indicators': positive_indicators,
        'safety_recommendations': safety_recommendations,
        'crisis_keywords': [kw for kw in crisis_keywords if kw in text_lower],
        'explanation': 'Analysis completed using keyword-based detection (AI service temporarily unavailable)'
    }

def get_conversation_summary(conversation_text: str) -> str:
    """
    Generate a brief summary of the conversation
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Summarize this conversation in 1-2 sentences, focusing on the relationship dynamic and communication style."},
                {"role": "user", "content": conversation_text}
            ],
            max_tokens=100,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except:
        return "Conversation analysis summary unavailable."