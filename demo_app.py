import streamlit as st
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="LoveGuard - AI Relationship Safety",
    page_icon="💕",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-first design
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .risk-score {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .low-risk {
        background-color: #d4edda;
        color: #155724;
    }
    .moderate-risk {
        background-color: #fff3cd;
        color: #856404;
    }
    .high-risk {
        background-color: #f8d7da;
        color: #721c24;
    }
    .crisis-alert {
        background-color: #721c24;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    .analysis-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #FF6B6B;
    }
    .safety-tip {
        background-color: #e7f3ff;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #007bff;
    }
    .stButton > button {
        background-color: #FF6B6B;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    if 'analysis_count' not in st.session_state:
        st.session_state.analysis_count = 0
    if 'user_tier' not in st.session_state:
        st.session_state.user_tier = 'free'
    if 'user_history' not in st.session_state:
        st.session_state.user_history = []

def display_header():
    st.markdown('<h1 class="main-header">💕 LoveGuard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Relationship Safety Analysis</p>', unsafe_allow_html=True)

def display_risk_score(score):
    if score <= 30:
        risk_class = "low-risk"
        risk_text = "LOW RISK"
    elif score <= 70:
        risk_class = "moderate-risk" 
        risk_text = "MODERATE RISK"
    else:
        risk_class = "high-risk"
        risk_text = "HIGH RISK"
    
    st.markdown(f'''
    <div class="risk-score {risk_class}">
        {score}/100<br>
        <small>{risk_text}</small>
    </div>
    ''', unsafe_allow_html=True)

def demo_analysis(text):
    """Demo analysis function"""
    text_lower = text.lower()
    
    # Simple keyword scoring for demo
    concerning_words = ['hurt', 'kill', 'stupid', 'worthless', 'control', 'forbid', 'stupid', 'crazy']
    positive_words = ['love', 'support', 'understand', 'respect', 'sorry']
    
    concern_score = sum(10 for word in concerning_words if word in text_lower)
    positive_score = sum(5 for word in positive_words if word in text_lower)
    
    risk_score = max(0, min(100, concern_score - positive_score + 10))
    
    red_flags = []
    if 'hurt' in text_lower or 'kill' in text_lower:
        red_flags.append("Threatening language detected")
    if 'stupid' in text_lower or 'worthless' in text_lower:
        red_flags.append("Verbal abuse patterns identified")
    if 'control' in text_lower or 'forbid' in text_lower:
        red_flags.append("Controlling behavior detected")
    
    positive_indicators = []
    if any(word in text_lower for word in positive_words):
        positive_indicators.append("Some positive communication elements found")
    
    safety_recommendations = []
    if risk_score > 70:
        safety_recommendations = [
            "Consider reaching out to domestic violence support services",
            "Document concerning conversations",
            "Create a safety plan with trusted contacts"
        ]
    elif risk_score > 40:
        safety_recommendations = [
            "Monitor communication patterns for escalation", 
            "Consider discussing concerns with trusted friends"
        ]
    else:
        safety_recommendations = [
            "Continue monitoring communication patterns",
            "Maintain healthy boundaries"
        ]
    
    return {
        'risk_score': risk_score,
        'red_flags': red_flags,
        'positive_indicators': positive_indicators,
        'safety_recommendations': safety_recommendations,
        'analysis_method': 'demo'
    }

def display_analysis_results(analysis_result):
    st.markdown("### 📊 Analysis Results")
    
    # Risk Score
    display_risk_score(analysis_result['risk_score'])
    
    # Red Flags
    if analysis_result['red_flags']:
        st.markdown("### 🚩 Red Flags Detected")
        for flag in analysis_result['red_flags']:
            st.markdown(f'<div class="analysis-card">⚠️ {flag}</div>', unsafe_allow_html=True)
    
    # Positive Indicators
    if analysis_result['positive_indicators']:
        st.markdown("### ✅ Positive Indicators")
        for indicator in analysis_result['positive_indicators']:
            st.markdown(f'<div class="analysis-card">💚 {indicator}</div>', unsafe_allow_html=True)
    
    # Safety Recommendations
    if analysis_result['safety_recommendations']:
        st.markdown("### 🛡️ Safety Recommendations")
        for rec in analysis_result['safety_recommendations']:
            st.markdown(f'<div class="safety-tip">💡 {rec}</div>', unsafe_allow_html=True)

def main():
    initialize_session_state()
    display_header()
    
    # Demo notice
    st.info("🎮 **Demo Mode** - This shows how LoveGuard works. In production, it uses advanced AI analysis.")
    
    # Free tier limitations
    if st.session_state.user_tier == 'free' and st.session_state.analysis_count >= 3:
        st.warning("You've reached your free analysis limit!")
        
        st.markdown("### 🌟 Upgrade to Premium")
        st.write("• Unlimited conversation analyses")
        st.write("• Detailed psychological insights")
        st.write("• Trend tracking and history")
        st.write("• Priority customer support")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Monthly - $9.99/month"):
                st.success("Payment processing... (Demo mode)")
                st.session_state.user_tier = 'premium'
                st.rerun()
        with col2:
            if st.button("Annual - $99.99/year"):
                st.success("Payment processing... (Demo mode)")
                st.session_state.user_tier = 'premium'
                st.rerun()
        return
    
    # Input section
    st.markdown("### 💬 Enter Conversation to Analyze")
    conversation_text = st.text_area(
        "Paste your conversation here:",
        height=200,
        placeholder="Paste text messages, emails, or any communication you'd like analyzed..."
    )
    
    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        include_context = st.checkbox("Include relationship context", value=True)
    with col2:
        detailed_analysis = st.checkbox("Detailed analysis", value=st.session_state.user_tier == 'premium')
    
    if st.session_state.user_tier == 'free' and detailed_analysis:
        st.info("Detailed analysis requires premium subscription")
        detailed_analysis = False
    
    # Sample conversations for demo
    st.markdown("**Try these sample conversations:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("😊 Healthy Example"):
            conversation_text = "I love you and I support your decisions. What do you think about going out with your friends tonight? I trust you completely."
    
    with col2:
        if st.button("⚠️ Concerning Example"):
            conversation_text = "You can't go out with your friends. I forbid you from seeing them. You belong to me and need to ask my permission."
    
    with col3:
        if st.button("🚨 Crisis Example"):
            conversation_text = "I'm going to hurt you if you try to leave me. You're worthless and nobody will love you like I do."
    
    # Analyze button
    if st.button("🔍 Analyze Conversation", disabled=not conversation_text):
        if conversation_text:
            with st.spinner("Analyzing conversation for safety concerns..."):
                # Demo analysis
                analysis_result = demo_analysis(conversation_text)
                
                # Crisis alert for high risk
                if analysis_result['risk_score'] > 70:
                    st.markdown('''
                    <div class="crisis-alert">
                        🆘 HIGH RISK DETECTED<br>
                        Please consider reaching out for help:<br>
                        📞 National Domestic Violence Hotline: 1-800-799-7233
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Display analysis
                display_analysis_results(analysis_result)
                
                # Update usage
                st.session_state.analysis_count += 1
                
                # Save to history
                st.session_state.user_history.append({
                    'timestamp': datetime.now(),
                    'risk_score': analysis_result['risk_score'],
                    'text_preview': conversation_text[:50] + "..." if len(conversation_text) > 50 else conversation_text
                })
                
                # Usage counter for free users
                if st.session_state.user_tier == 'free':
                    remaining = 3 - st.session_state.analysis_count
                    if remaining > 0:
                        st.info(f"Free analyses remaining: {remaining}")
                    else:
                        st.warning("Free limit reached! Upgrade for unlimited access.")
    
    # Premium features section
    if st.session_state.user_tier == 'free':
        st.markdown("---")
        st.markdown("### 🌟 Premium Features")
        st.write("• Unlimited conversation analyses")
        st.write("• Detailed psychological insights")
        st.write("• Trend tracking and history")
        st.write("• Priority customer support")
        st.write("• Export reports to PDF")
        
        if st.button("Get Premium Access - $9.99/month"):
            st.info("In production, this would redirect to Stripe payment processing")
    
    # History section for premium users
    if st.session_state.user_tier == 'premium' and st.session_state.user_history:
        st.markdown("---")
        st.markdown("### 📈 Your Analysis History")
        for i, item in enumerate(reversed(st.session_state.user_history[-5:])):  # Show last 5
            st.write(f"**{item['timestamp'].strftime('%Y-%m-%d %H:%M')}** - Risk Score: {item['risk_score']} - \"{item['text_preview']}\"")
    
    # Footer
    st.markdown("---")
    st.markdown("**Disclaimer:** LoveGuard is for informational purposes only. In emergency situations, contact local authorities or emergency services immediately.")
    
    # Emergency contacts
    with st.expander("🆘 Emergency Resources"):
        st.write("**National Domestic Violence Hotline:** 1-800-799-7233")
        st.write("**Crisis Text Line:** Text HOME to 741741")
        st.write("**National Suicide Prevention Lifeline:** 988")
        st.write("**Emergency Services:** 911")

if __name__ == "__main__":
    main()