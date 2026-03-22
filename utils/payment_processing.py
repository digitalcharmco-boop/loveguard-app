import stripe
import os
from typing import Dict, Optional

# Set Stripe API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_payment_intent(amount: int, currency: str = 'usd') -> Optional[Dict]:
    """
    Create a Stripe payment intent
    Args:
        amount: Amount in cents (e.g., 999 for $9.99)
        currency: Currency code (default: 'usd')
    Returns:
        Payment intent dict or None if error
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata={
                'product': 'LoveGuard Premium Subscription',
                'type': 'monthly_subscription'
            }
        )
        return {
            'id': intent.id,
            'client_secret': intent.client_secret,
            'amount': intent.amount,
            'status': intent.status
        }
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return None
    except Exception as e:
        print(f"Payment error: {e}")
        return None

def verify_payment(payment_intent_id: str) -> bool:
    """
    Verify that a payment was successful
    Args:
        payment_intent_id: Stripe payment intent ID
    Returns:
        True if payment succeeded, False otherwise
    """
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent.status == 'succeeded'
    except stripe.error.StripeError as e:
        print(f"Stripe verification error: {e}")
        return False
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def create_subscription(customer_email: str, price_id: str) -> Optional[Dict]:
    """
    Create a subscription for a customer
    Args:
        customer_email: Customer's email address
        price_id: Stripe price ID for the subscription
    Returns:
        Subscription dict or None if error
    """
    try:
        # Create or retrieve customer
        customers = stripe.Customer.list(email=customer_email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(email=customer_email)
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent']
        )
        
        return {
            'subscription_id': subscription.id,
            'customer_id': customer.id,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret,
            'status': subscription.status
        }
    except stripe.error.StripeError as e:
        print(f"Stripe subscription error: {e}")
        return None
    except Exception as e:
        print(f"Subscription error: {e}")
        return None

def cancel_subscription(subscription_id: str) -> bool:
    """
    Cancel a subscription
    Args:
        subscription_id: Stripe subscription ID
    Returns:
        True if cancellation succeeded, False otherwise
    """
    try:
        subscription = stripe.Subscription.delete(subscription_id)
        return subscription.status == 'canceled'
    except stripe.error.StripeError as e:
        print(f"Stripe cancellation error: {e}")
        return False
    except Exception as e:
        print(f"Cancellation error: {e}")
        return False

def get_customer_subscriptions(customer_email: str) -> list:
    """
    Get all subscriptions for a customer
    Args:
        customer_email: Customer's email address
    Returns:
        List of subscription dicts
    """
    try:
        customers = stripe.Customer.list(email=customer_email, limit=1)
        if not customers.data:
            return []
        
        customer = customers.data[0]
        subscriptions = stripe.Subscription.list(customer=customer.id)
        
        return [{
            'id': sub.id,
            'status': sub.status,
            'current_period_end': sub.current_period_end,
            'cancel_at_period_end': sub.cancel_at_period_end
        } for sub in subscriptions.data]
    except stripe.error.StripeError as e:
        print(f"Stripe error getting subscriptions: {e}")
        return []
    except Exception as e:
        print(f"Error getting subscriptions: {e}")
        return []

def create_stripe_prices():
    """
    Create Stripe prices for LoveGuard products (run once during setup)
    """
    try:
        # Monthly subscription price
        monthly_price = stripe.Price.create(
            unit_amount=999,  # $9.99
            currency='usd',
            recurring={'interval': 'month'},
            product_data={
                'name': 'LoveGuard Premium Monthly',
                'description': 'Unlimited AI relationship analysis with premium features'
            }
        )
        
        # Annual subscription price (discounted)
        annual_price = stripe.Price.create(
            unit_amount=9999,  # $99.99 (17% discount)
            currency='usd', 
            recurring={'interval': 'year'},
            product_data={
                'name': 'LoveGuard Premium Annual',
                'description': 'Unlimited AI relationship analysis with premium features (Annual billing)'
            }
        )
        
        # One-time analysis price
        single_price = stripe.Price.create(
            unit_amount=299,  # $2.99
            currency='usd',
            product_data={
                'name': 'LoveGuard Single Analysis',
                'description': 'One-time AI relationship safety analysis'
            }
        )
        
        return {
            'monthly_price_id': monthly_price.id,
            'annual_price_id': annual_price.id,
            'single_price_id': single_price.id
        }
    except stripe.error.StripeError as e:
        print(f"Stripe error creating prices: {e}")
        return None
    except Exception as e:
        print(f"Error creating prices: {e}")
        return None

def handle_webhook_event(event_dict: Dict) -> bool:
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
            # Handle successful payment
            payment_intent = event_dict['data']['object']
            print(f"Payment succeeded: {payment_intent['id']}")
            # Update user's premium status in database
            return True
            
        elif event_type == 'subscription.created':
            # Handle new subscription
            subscription = event_dict['data']['object']
            print(f"Subscription created: {subscription['id']}")
            # Update user's subscription status in database
            return True
            
        elif event_type == 'subscription.deleted':
            # Handle subscription cancellation
            subscription = event_dict['data']['object']
            print(f"Subscription canceled: {subscription['id']}")
            # Update user's subscription status in database
            return True
            
        elif event_type == 'invoice.payment_failed':
            # Handle failed payment
            invoice = event_dict['data']['object']
            print(f"Payment failed for invoice: {invoice['id']}")
            # Notify user and potentially suspend service
            return True
            
        else:
            print(f"Unhandled event type: {event_type}")
            return False
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return False