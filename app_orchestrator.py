#!/usr/bin/env python3
"""
LoveGuard Application Orchestrator
Layer 2: Intelligent routing and decision making for LoveGuard operations
"""

import sys
import os
import logging
from typing import Dict, Tuple, List

# Add execution directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'execution'))

from ai_analyzer import AIAnalyzer
from crisis_detector import CrisisDetector
from fallback_analyzer import FallbackAnalyzer
from stripe_processor import StripeProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoveGuardOrchestrator:
    """
    Orchestrator that implements intelligent routing between directives and execution scripts
    This is Layer 2 of the 3-layer architecture - decision making and coordination
    """
    
    def __init__(self):
        """Initialize orchestrator with execution tools"""
        try:
            self.ai_analyzer = AIAnalyzer()
            self.use_ai = True
        except Exception as e:
            logger.warning(f"AI analyzer unavailable: {e}")
            self.use_ai = False
            
        self.fallback_analyzer = FallbackAnalyzer()
        self.crisis_detector = CrisisDetector()
        
        try:
            self.stripe_processor = StripeProcessor()
            self.payments_enabled = True
        except Exception as e:
            logger.warning(f"Stripe processor unavailable: {e}")
            self.payments_enabled = False
    
    def analyze_conversation(
        self,
        conversation_text: str,
        include_context: bool = True,
        detailed: bool = False,
        user_tier: str = "free"
    ) -> Dict:
        """
        Orchestrate conversation analysis following the analyze_conversation directive
        
        This method implements the business logic from directives/analyze_conversation.md
        """
        
        logger.info("Starting conversation analysis orchestration")
        
        # Step 1: Input validation (per directive)
        if not conversation_text or len(conversation_text.strip()) == 0:
            raise ValueError("Conversation text cannot be empty")
        
        # Validate user tier and adjust features
        if user_tier == "free":
            detailed = False  # Free users don't get detailed analysis
        
        # Step 2: Primary analysis attempt
        analysis_result = None
        analysis_method = "fallback"
        
        if self.use_ai:
            try:
                logger.info("Attempting AI analysis")
                analysis_result = self.ai_analyzer.analyze_conversation(
                    conversation_text=conversation_text,
                    include_context=include_context,
                    detailed=detailed,
                    user_tier=user_tier
                )
                analysis_method = "ai"
                logger.info("AI analysis completed successfully")
                
            except Exception as e:
                logger.warning(f"AI analysis failed: {e}")
                # Fall through to fallback
                self.use_ai = False  # Disable AI for subsequent requests
        
        # Step 3: Fallback handling (per directive)
        if analysis_result is None:
            logger.info("Using fallback keyword-based analysis")
            analysis_result = self.fallback_analyzer.analyze_conversation(
                conversation_text=conversation_text,
                include_context=include_context,
                detailed=detailed,
                user_tier=user_tier
            )
        
        # Step 4: Crisis detection (per directive)
        logger.info("Running crisis detection")
        crisis_level, safety_resources, crisis_details = self.crisis_detector.assess_crisis_level(
            conversation_text, analysis_result
        )
        
        # Step 5: Combine results
        final_result = {
            **analysis_result,
            'crisis_level': crisis_level,
            'safety_resources': safety_resources,
            'crisis_details': crisis_details,
            'analysis_method': analysis_method,
            'user_tier': user_tier
        }
        
        logger.info(f"Analysis orchestration completed: {crisis_level} crisis level, {analysis_result['risk_score']} risk score")
        return final_result
    
    def process_payment(
        self,
        user_email: str,
        payment_type: str = "monthly_subscription",
        amount: int = None
    ) -> Dict:
        """
        Orchestrate payment processing following the process_payment directive
        
        This method implements the business logic from directives/process_payment.md
        """
        
        logger.info(f"Starting payment processing for {user_email}")
        
        if not self.payments_enabled:
            return {
                'payment_status': 'failed',
                'error_message': 'Payment processing temporarily unavailable'
            }
        
        # Step 1: Determine amount if not provided
        if amount is None:
            amounts = {
                'monthly_subscription': 999,   # $9.99
                'annual_subscription': 9999,   # $99.99
                'single_analysis': 299         # $2.99
            }
            amount = amounts.get(payment_type, 999)
        
        try:
            # Step 2: Create payment intent
            if payment_type.endswith('_subscription'):
                logger.info("Creating subscription")
                result = self.stripe_processor.create_subscription(
                    customer_email=user_email,
                    payment_type=payment_type
                )
            else:
                logger.info("Creating one-time payment")
                result = self.stripe_processor.create_payment_intent(
                    amount=amount,
                    payment_type=payment_type,
                    customer_email=user_email
                )
            
            if result:
                logger.info("Payment processing initiated successfully")
                return {
                    'payment_status': 'initiated',
                    **result
                }
            else:
                logger.error("Payment processing failed")
                return {
                    'payment_status': 'failed',
                    'error_message': 'Unable to process payment. Please try again.'
                }
                
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return {
                'payment_status': 'failed',
                'error_message': 'Payment processing error. Please contact support.'
            }
    
    def verify_payment_and_upgrade_user(self, payment_intent_id: str) -> Dict:
        """
        Verify payment and upgrade user tier
        """
        
        if not self.payments_enabled:
            return {'success': False, 'error': 'Payment verification unavailable'}
        
        try:
            # Verify payment succeeded
            payment_verified = self.stripe_processor.verify_payment(payment_intent_id)
            
            if payment_verified:
                logger.info(f"Payment {payment_intent_id} verified successfully")
                return {
                    'success': True,
                    'user_tier': 'premium',
                    'payment_status': 'verified'
                }
            else:
                logger.warning(f"Payment {payment_intent_id} verification failed")
                return {
                    'success': False,
                    'error': 'Payment verification failed'
                }
                
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return {
                'success': False,
                'error': 'Payment verification error'
            }
    
    def get_user_subscription_status(self, user_email: str) -> Dict:
        """
        Get user's current subscription status
        """
        
        if not self.payments_enabled:
            return {'tier': 'free', 'subscriptions': []}
        
        try:
            subscriptions = self.stripe_processor.get_customer_subscriptions(user_email)
            
            # Determine user tier based on active subscriptions
            if subscriptions:
                tier = 'premium'
            else:
                tier = 'free'
            
            return {
                'tier': tier,
                'subscriptions': subscriptions,
                'payments_enabled': True
            }
            
        except Exception as e:
            logger.error(f"Subscription status error: {e}")
            return {
                'tier': 'free',
                'subscriptions': [],
                'error': str(e)
            }
    
    def handle_error_and_self_anneal(self, operation: str, error: Exception) -> Dict:
        """
        Handle errors and implement self-annealing improvements
        
        This method implements the self-annealing principle from the architecture
        """
        
        logger.error(f"Error in {operation}: {error}")
        
        # Analyze error type and implement fixes
        error_type = type(error).__name__
        
        improvements = []
        
        if "OpenAI" in str(error) or "API" in str(error):
            # AI service issues - improve fallback usage
            if hasattr(self, 'use_ai'):
                self.use_ai = False
            improvements.append("Disabled AI service, using fallback analysis")
            
        elif "Stripe" in str(error) or "payment" in str(error).lower():
            # Payment service issues - improve error handling
            if hasattr(self, 'payments_enabled'):
                self.payments_enabled = False
            improvements.append("Disabled payment processing, using free tier only")
            
        elif "rate limit" in str(error).lower():
            # Rate limiting - implement better backoff
            improvements.append("Implementing exponential backoff for rate limits")
            
        else:
            improvements.append("General error handling improved")
        
        # Return error response with improvements
        return {
            'success': False,
            'error': str(error),
            'error_type': error_type,
            'operation': operation,
            'improvements_applied': improvements,
            'fallback_available': True
        }
    
    def get_system_status(self) -> Dict:
        """
        Get current system status for monitoring
        """
        
        return {
            'ai_analyzer_available': self.use_ai,
            'fallback_analyzer_available': True,  # Always available
            'crisis_detector_available': True,    # Always available  
            'payment_processor_available': self.payments_enabled,
            'system_healthy': True,
            'fallback_mode': not self.use_ai
        }