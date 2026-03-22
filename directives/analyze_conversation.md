# Analyze Conversation Directive

## Goal
Analyze user-provided conversation text for relationship red flags, manipulation patterns, and safety concerns using AI.

## Inputs
- `conversation_text` (string): Raw conversation text from user
- `include_context` (boolean): Whether to consider broader relationship context
- `detailed_analysis` (boolean): Whether to provide detailed psychological insights (premium feature)
- `user_tier` (string): "free" or "premium" to determine analysis depth

## Tools/Scripts to Use
- `execution/ai_analyzer.py` - Main OpenAI API integration
- `execution/crisis_detector.py` - Crisis keyword detection and safety assessment
- `execution/fallback_analyzer.py` - Keyword-based analysis when AI unavailable

## Process Flow
1. **Input Validation**
   - Check conversation_text is not empty
   - Validate user tier and feature access
   - Sanitize input for API safety

2. **Primary Analysis**
   - Call `execution/ai_analyzer.py` with OpenAI GPT-4
   - Pass analysis parameters based on user tier
   - Handle API errors gracefully

3. **Crisis Detection**
   - Run `execution/crisis_detector.py` on results
   - Check for immediate safety concerns
   - Generate appropriate safety resources

4. **Fallback Handling**
   - If OpenAI fails, use `execution/fallback_analyzer.py`
   - Provide keyword-based analysis
   - Maintain service availability

## Expected Outputs
```json
{
  "risk_score": 0-100,
  "red_flags": ["specific concerning behaviors"],
  "positive_indicators": ["healthy patterns found"],
  "safety_recommendations": ["actionable advice"],
  "crisis_level": "immediate|high|moderate|low",
  "safety_resources": ["emergency contacts and resources"],
  "analysis_method": "ai|fallback"
}
```

## Edge Cases
- **API Rate Limits**: Use exponential backoff, fall back to keyword analysis
- **Empty Input**: Return error with helpful message
- **Extremely Long Text**: Truncate to token limits, warn user
- **Non-English Text**: Handle gracefully, may have reduced accuracy
- **Crisis Language**: Immediately escalate, provide emergency resources
- **API Key Missing**: Fall back to keyword analysis, log warning

## Success Criteria
- Analysis completes within 10 seconds
- Risk score is between 0-100
- Crisis detection triggers appropriate resources
- Fallback maintains 80%+ service availability
- No user data logged permanently

## Error Handling
- OpenAI API errors → fallback analysis
- Network timeouts → retry once, then fallback
- Invalid input → return structured error
- Rate limits → exponential backoff up to 30 seconds

## Rate Limits & Constraints
- OpenAI: 3 requests/minute on free tier
- Max input: 4000 characters (GPT-4 token limit consideration)
- Response timeout: 30 seconds maximum
- Free users: 3 analyses/day, premium: unlimited

## Monitoring
- Track API response times
- Monitor fallback usage rates
- Log analysis completion rates
- Alert on high error rates (>10%)

## Updates Needed
- When OpenAI changes models or pricing
- If crisis keywords need expansion
- When new safety resources become available
- If fallback accuracy drops below 70%