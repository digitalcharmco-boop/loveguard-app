# Process Payment Directive

## Goal
Handle user subscription upgrades and payments through Stripe integration while maintaining security and reliability.

## Inputs
- `user_email` (string): Customer email address
- `payment_type` (string): "monthly_subscription", "annual_subscription", or "single_analysis"
- `amount` (integer): Payment amount in cents
- `payment_method_id` (string): Stripe payment method ID from frontend

## Tools/Scripts to Use
- `execution/stripe_processor.py` - Main Stripe payment handling
- `execution/subscription_manager.py` - Subscription lifecycle management
- `execution/user_tier_updater.py` - Update user access levels

## Process Flow
1. **Payment Intent Creation**
   - Call `execution/stripe_processor.py create_payment_intent()`
   - Generate secure payment intent with proper metadata
   - Return client_secret for frontend confirmation

2. **Payment Verification**
   - Verify payment completion via webhook or polling
   - Validate payment matches expected amount and type
   - Handle payment failures gracefully

3. **User Access Update**
   - Call `execution/user_tier_updater.py`
   - Upgrade user from "free" to "premium" tier
   - Update session state and database records

4. **Subscription Management**
   - For subscriptions, call `execution/subscription_manager.py`
   - Set up recurring billing and cancellation handling
   - Configure proration for plan changes

## Expected Outputs
```json
{
  "payment_status": "succeeded|failed|processing",
  "subscription_id": "stripe_subscription_id",
  "client_secret": "stripe_client_secret",
  "user_tier": "free|premium",
  "next_billing_date": "ISO_date",
  "error_message": "human_readable_error"
}
```

## Edge Cases
- **Failed Payments**: Retry logic, clear error messages, maintain free access
- **Webhook Delays**: Implement polling backup for payment verification
- **Duplicate Payments**: Idempotency keys, check existing subscriptions
- **Plan Downgrades**: Handle cancellations, maintain access until period end
- **Currency Mismatches**: Validate USD amounts, reject invalid currencies
- **Fraud Detection**: Use Stripe Radar, block suspicious transactions

## Success Criteria
- Payment processing completes within 30 seconds
- 99.9% payment verification accuracy
- Zero duplicate charges
- Clear error messages for failed payments
- Immediate tier upgrades on successful payment

## Error Handling
- Network failures → retry with exponential backoff
- Invalid payment methods → clear user-friendly errors
- Stripe API errors → log details, show generic error to user
- Webhook failures → fall back to polling verification
- Database errors → rollback payment, notify user

## Security Requirements
- Never store credit card information
- Use Stripe's secure payment forms
- Validate all webhooks with signatures
- Log payment events for audit (no sensitive data)
- Implement proper HTTPS throughout

## Rate Limits & Constraints
- Stripe: 100 requests/second
- Payment intents expire after 24 hours
- Webhooks must respond within 20 seconds
- Maximum retry attempts: 3 per operation

## Monitoring
- Track payment success/failure rates
- Monitor webhook response times
- Alert on high failure rates (>5%)
- Track subscription churn metrics
- Monitor for unusual payment patterns

## Compliance
- PCI DSS compliance via Stripe
- GDPR: Handle data deletion requests
- Store minimal payment metadata only
- Proper receipt generation and storage

## Updates Needed
- When Stripe API versions change
- If pricing plans are modified
- When new payment methods are supported
- If tax requirements change by jurisdiction