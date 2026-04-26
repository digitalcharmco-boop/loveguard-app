import streamlit as st
import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add current directory to Python path for orchestrator
sys.path.append(os.path.dirname(__file__))

# Load secrets from Streamlit Cloud secrets into env vars (if available)
try:
    _secrets = st.secrets
    for _key in ["OPENAI_API_KEY", "STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY",
                 "APP_ENV", "DEBUG", "GOOGLE_CLOUD_PROJECT"]:
        if _key in _secrets and not os.environ.get(_key):
            os.environ[_key] = str(_secrets[_key])
except Exception:
    pass  # Running locally with .env file — that's fine

from app_orchestrator import LoveGuardOrchestrator

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
    .stTextArea textarea {
        border-radius: 10px;
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
    .mobile-container {
        max-width: 100%;
        padding: 0.5rem;
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
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = LoveGuardOrchestrator()

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

def display_crisis_alert(crisis_level, resources):
    if crisis_level == "immediate":
        st.markdown(f'''
        <div class="crisis-alert">
            🆘 IMMEDIATE SAFETY CONCERN DETECTED<br>
            Please seek help immediately:<br>
            📞 National Domestic Violence Hotline: 1-800-799-7233
        </div>
        ''', unsafe_allow_html=True)
    
    if resources:
        st.markdown("### 🆘 Safety Resources")
        for resource in resources:
            st.markdown(f"• {resource}")

def handle_payment_upgrade():
    st.markdown("### 🌟 Upgrade to Premium")
    st.write("Get unlimited analyses, detailed reports, and priority support!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Monthly - $9.99/month"):
            result = st.session_state.orchestrator.process_payment(
                user_email="user@example.com",  # In production, get from user auth
                payment_type="monthly_subscription"
            )
            if result.get('payment_status') == 'initiated':
                st.success("Payment processing... (Demo mode)")
                st.session_state.user_tier = 'premium'
                st.rerun()
            else:
                st.error(result.get('error_message', 'Payment failed'))
    
    with col2:
        if st.button("Annual - $99.99/year"):
            result = st.session_state.orchestrator.process_payment(
                user_email="user@example.com",  # In production, get from user auth
                payment_type="annual_subscription"
            )
            if result.get('payment_status') == 'initiated':
                st.success("Payment processing... (Demo mode)")
                st.session_state.user_tier = 'premium'
                st.rerun()
            else:
                st.error(result.get('error_message', 'Payment failed'))

def main():
    initialize_session_state()
    display_header()
    
    # Free tier limitations
    if st.session_state.user_tier == 'free' and st.session_state.analysis_count >= 3:
        st.warning("You've reached your free analysis limit!")
        handle_payment_upgrade()
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
    
    # Analyze button
    if st.button("🔍 Analyze Conversation", disabled=not conversation_text):
        if conversation_text:
            with st.spinner("Analyzing conversation for safety concerns..."):
                try:
                    # Use orchestrator for analysis (follows directive)
                    analysis_result = st.session_state.orchestrator.analyze_conversation(
                        conversation_text=conversation_text,
                        include_context=include_context,
                        detailed=detailed_analysis,
                        user_tier=st.session_state.user_tier
                    )
                    
                    # Extract crisis information
                    crisis_level = analysis_result.get('crisis_level', 'low')
                    safety_resources = analysis_result.get('safety_resources', [])
                    
                    # Display crisis alert if needed
                    if crisis_level in ["immediate", "high"]:
                        display_crisis_alert(crisis_level, safety_resources)
                    
                    # Display main analysis
                    display_analysis_results(analysis_result)
                    
                    # Update usage
                    st.session_state.analysis_count += 1
                    
                    # Save to history
                    st.session_state.user_history.append({
                        'timestamp': datetime.now(),
                        'risk_score': analysis_result['risk_score'],
                        'crisis_level': crisis_level,
                        'analysis_method': analysis_result.get('analysis_method', 'unknown')
                    })
                    
                    # Usage counter for free users
                    if st.session_state.user_tier == 'free':
                        remaining = 3 - st.session_state.analysis_count
                        if remaining > 0:
                            st.info(f"Free analyses remaining: {remaining}")
                        else:
                            st.warning("Free limit reached! Upgrade for unlimited access.")
                    
                    # Show analysis method for transparency
                    if analysis_result.get('analysis_method') == 'fallback':
                        st.info("🔄 Analysis completed using backup system (AI temporarily unavailable)")
                    
                except Exception as e:
                    # Use orchestrator's error handling
                    error_result = st.session_state.orchestrator.handle_error_and_self_anneal(
                        "analyze_conversation", e
                    )
                    st.error(f"Analysis failed: {str(e)}")
                    if error_result.get('fallback_available'):
                        st.info("Fallback analysis system is still available. Please try again.")
                    else:
                        st.info("Please contact support if the issue persists.")
    
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
            handle_payment_upgrade()
    
    # History section for premium users
    if st.session_state.user_tier == 'premium' and st.session_state.user_history:
        st.markdown("---")
        st.markdown("### 📈 Your Analysis History")
        df = pd.DataFrame(st.session_state.user_history)
        st.line_chart(df.set_index('timestamp')['risk_score'])
    
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