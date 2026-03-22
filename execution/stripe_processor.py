#!/usr/bin/env python3
"""
LoveGuard Stripe Payment Processor
Deterministic script for handling payments and subscriptions via Stripe
"""

import stripe
import os
import logging
import time
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StripeProcessor:
    def __init__(self):
        """Initialize Stripe processor with API configuration"""
        self.secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable not set")
            
        stripe.api_key = self.secret_key
        
        # Price configurations (in cents)
        self.prices = {
            'monthly_subscription': 999,  # $9.99
            'annual_subscription': 9999,  # $99.99 (17% discount)
            'single_analysis': 299       # $2.99
        }
        
        self.max_retries = 3
        self.retry_delay = 1
    
    def create_payment_intent(
        self, 
        amount: int, 
        currency: str = 'usd',
        payment_type: str = 'single_analysis',
        customer_email: str = None
    ) -> Optional[Dict]:
        """
        Create a Stripe payment intent
        
        Args:
            amount: Amount in cents
            currency: Currency code (default: 'usd')
            payment_type: Type of payment for metadata
            customer_email: Optional customer email
            
        Returns:
            Payment intent dictionary or None if error
        """
        
        try:
            # Build metadata
            metadata = {
                'product': 'LoveGuard Premium',
                'type': payment_type,
                'service': 'relationship_safety_analysis'
            }
            
            if customer_email:
                metadata['customer_email'] = customer_email
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata,
                automatic_payment_methods={'enabled': True},
                description=f"LoveGuard {payment_type.replace('_', ' ').title()}"
            )
            
            result = {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'amount': intent.amount,
                'status': intent.status,
                'currency': intent.currency
            }
            
            logger.info(f"Payment intent created: {intent.id}")
            return result
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            return None
    
    def verify_payment(self, payment_intent_id: str) -> bool:
        """
        Verify that a payment was successful
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            True if payment succeeded, False otherwise
        """
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            is_successful = intent.status == 'succeeded'
            
            logger.info(f"Payment verification for {payment_intent_id}: {intent.status}")
            return is_successful
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe verification error: {e}")
            return False
        except Exception as e:
            logger.error(f"Payment verification error: {e}")
            return False
    
    def create_subscription(
        self, 
        customer_email: str, 
        payment_type: str = 'monthly_subscription'
    ) -> Optional[Dict]:
        """
        Create a subscription for a customer
        
        Args:
            customer_email: Customer's email address
            payment_type: 'monthly_subscription' or 'annual_subscription'
            
        Returns:
            Subscription dictionary or None if error
        """
        
        try:
            # Get or create customer
            customer = self._get_or_create_customer(customer_email)
            if not customer:
                return None
            
            # Get price amount
            amount = self.prices.get(payment_type)
            if not amount:
                logger.error(f"Unknown payment type: {payment_type}")
                return None
            
            # Determine interval
            interval = 'month' if payment_type == 'monthly_subscription' else 'year'
            
            # Create price object (or use existing price ID in production)
            price = stripe.Price.create(
                unit_amount=amount,
                currency='usd',
                recurring={'interval': interval},
                product_data={
                    'name': f'LoveGuard Premium ({interval.title()}ly)',
                    'description': 'Unlimited AI relationship analysis with premium features'
                }
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price.id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'product': 'LoveGuard Premium',
                    'type': payment_type
                }
            )
            
            result = {
                'subscription_id': subscription.id,
                'customer_id': customer.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'amount': amount,
                'interval': interval
            }
            
            logger.info(f"Subscription created: {subscription.id}")
            return result
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription error: {e}")
            return None
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, immediate: bool = False) -> bool:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            immediate: If True, cancel immediately; if False, at period end
            
        Returns:
            True if cancellation succeeded, False otherwise
        """
        
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
                logger.info(f"Subscription {subscription_id} canceled immediately")
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Subscription {subscription_id} set to cancel at period end")
            
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe cancellation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Cancellation error: {e}")
            return False
    
    def get_customer_subscriptions(self, customer_email: str) -> List[Dict]:
        """
        Get all active subscriptions for a customer
        
        Args:
            customer_email: Customer's email address
            
        Returns:
            List of subscription dictionaries
        """
        
        try:
            # Find customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if not customers.data:
                return []
            
            customer = customers.data[0]
            
            # Get subscriptions
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                status='active'
            )
            
            result = []
            for sub in subscriptions.data:
                result.append({
                    'id': sub.id,
                    'status': sub.status,
                    'current_period_end': sub.current_period_end,
                    'current_period_start': sub.current_period_start,
                    'cancel_at_period_end': sub.cancel_at_period_end,
                    'amount': sub.items.data[0].price.unit_amount if sub.items.data else 0,
                    'interval': sub.items.data[0].price.recurring.interval if sub.items.data else None
                })
            
            return result
            
        except stripe.error.StripeError as e:
            logger.error(f"Error getting subscriptions: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting subscriptions: {e}")
            return []
    
    def handle_webhook_event(self, event_dict: Dict) -> bool:
        """
        Handle Stripe webhook events
        
        Args:
            event_dict: Webhook event data from Stripe
            
        Returns:
            True if handled successfully, False otherwise
        """
        
        try:
            event_type = event_dict.get('type')
            
            if event_type == 'payment_intent.succeeded':
                payment_intent = event_dict['data']['object']
                logger.info(f"Payment succeeded: {payment_intent['id']}")
                # Additional logic for payment success handling
                return True
                
            elif event_type == 'subscription.created':
                subscription = event_dict['data']['object']
                logger.info(f"Subscription created: {subscription['id']}")
                # Additional logic for new subscription
                return True
                
            elif event_type == 'subscription.deleted':
                subscription = event_dict['data']['object']
                logger.info(f"Subscription canceled: {subscription['id']}")
                # Additional logic for cancellation
                return True
                
            elif event_type == 'invoice.payment_failed':
                invoice = event_dict['data']['object']
                logger.warning(f"Payment failed for invoice: {invoice['id']}")
                # Additional logic for failed payments
                return True
                
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    def _get_or_create_customer(self, email: str) -> Optional[stripe.Customer]:
        """Get existing customer or create new one"""
        
        try:
            # Check for existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
            
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                description="LoveGuard Premium Customer"
            )
            
            logger.info(f"Customer created: {customer.id}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Customer error: {e}")
            return None

def main():
    """Command line interface for testing"""
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python stripe_processor.py create_payment <amount> [type] [email]")
        print("  python stripe_processor.py verify_payment <payment_intent_id>")
        print("  python stripe_processor.py create_subscription <email> [type]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        processor = StripeProcessor()
        
        if command == 'create_payment':
            amount = int(sys.argv[2])
            payment_type = sys.argv[3] if len(sys.argv) > 3 else 'single_analysis'
            email = sys.argv[4] if len(sys.argv) > 4 else None
            
            result = processor.create_payment_intent(amount, payment_type=payment_type, customer_email=email)
            print(json.dumps(result, indent=2))
            
        elif command == 'verify_payment':
            payment_id = sys.argv[2]
            result = processor.verify_payment(payment_id)
            print(f"Payment verified: {result}")
            
        elif command == 'create_subscription':
            email = sys.argv[2]
            payment_type = sys.argv[3] if len(sys.argv) > 3 else 'monthly_subscription'
            
            result = processor.create_subscription(email, payment_type)
            print(json.dumps(result, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()