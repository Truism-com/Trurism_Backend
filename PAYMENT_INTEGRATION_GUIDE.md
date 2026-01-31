"""
Payment Integration Guide

This document explains how to integrate the Razorpay payment system with booking flow.

## Setup Instructions

### 1. Install Razorpay SDK
```bash
pip install razorpay
```

### 2. Configure Environment Variables
Add these to your `.env` file:
```env
# Get from: https://dashboard.razorpay.com/#/app/keys
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXX  # or rzp_live_XXXXXXXXXX for production
RAZORPAY_KEY_SECRET=YourSecretKeyHere

# Generate webhook secret in Razorpay Dashboard
RAZORPAY_WEBHOOK_SECRET=whsec_XXXXXXXXXX
```

### 3. Run Database Migration
```bash
# Apply migration to create payment tables
alembic upgrade head
```

### 4. Configure Razorpay Webhook
Go to: https://dashboard.razorpay.com/#/app/webhooks

- **Webhook URL**: `https://yourdomain.com/payments/webhook`
- **Secret**: Generate and copy to `RAZORPAY_WEBHOOK_SECRET`
- **Events to Enable**:
  - `payment.captured`
  - `payment.failed`
  - `order.paid`
  - `refund.processed`

## Usage Flow

### Frontend Integration

#### Step 1: Load Razorpay Checkout Script
```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

#### Step 2: Create Order
```javascript
async function initiatePayment(bookingId, bookingType, baseAmount, paymentMethod) {
    const response = await fetch('/payments/create-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
            booking_id: bookingId,
            booking_type: bookingType,
            base_amount: baseAmount,
            payment_method: paymentMethod  // 'card', 'upi', 'netbanking', etc.
        })
    });
    
    const orderData = await response.json();
    
    // Show fee breakdown to user
    console.log('Base Amount:', orderData.base_amount);
    console.log('Convenience Fee:', orderData.convenience_fee);
    console.log('GST:', orderData.taxes);
    console.log('Total:', orderData.total_amount);
    
    // Open Razorpay checkout
    openRazorpayCheckout(orderData);
}
```

#### Step 3: Open Razorpay Checkout
```javascript
function openRazorpayCheckout(orderData) {
    const options = {
        key: orderData.key_id,
        amount: orderData.amount,  // Amount in paise
        currency: orderData.currency,
        order_id: orderData.order_id,
        name: 'Your Travel Agency',
        description: 'Flight Booking Payment',
        image: '/logo.png',
        handler: function(response) {
            // Payment successful - verify signature
            verifyPayment(response);
        },
        prefill: {
            name: user.name,
            email: user.email,
            contact: user.phone
        },
        theme: {
            color: '#3399cc'
        },
        modal: {
            ondismiss: function() {
                // User closed checkout without paying
                alert('Payment cancelled');
            }
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}
```

#### Step 4: Verify Payment
```javascript
async function verifyPayment(razorpayResponse) {
    try {
        const response = await fetch('/payments/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                razorpay_order_id: razorpayResponse.razorpay_order_id,
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Payment verified successfully
            alert('Payment successful! Booking confirmed.');
            // Redirect to booking details page
            window.location.href = `/bookings/${result.booking_id}`;
        } else {
            alert('Payment verification failed: ' + result.message);
        }
    } catch (error) {
        console.error('Verification error:', error);
        alert('Payment verification failed. Please contact support.');
    }
}
```

## Backend Integration

### Modified Booking Flow

The booking creation has been split into two steps:

#### Old Flow (Mock Payment):
1. Create booking with payment processing in one step
2. Mock payment success/failure

#### New Flow (Real Payment):
1. **Create booking with PENDING status**
2. **Create Razorpay order** via `/payments/create-order`
3. **User completes payment** on Razorpay checkout
4. **Verify payment** via `/payments/verify`
5. **Update booking to CONFIRMED**

### Example: Modified Flight Booking

```python
# Step 1: Create booking with PENDING status (do NOT process payment yet)
@router.post("/bookings/flights/initiate")
async def initiate_flight_booking(
    booking_request: FlightBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    # Create booking with PENDING status
    booking = FlightBooking(
        booking_reference=generate_reference(),
        user_id=current_user.id,
        status=BookingStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        # ... other fields
    )
    db.add(booking)
    await db.commit()
    
    # Return booking ID for payment
    return {
        "booking_id": booking.id,
        "booking_type": "flight",
        "amount": booking.total_amount
    }

# Step 2: Frontend calls /payments/create-order
# Step 3: Frontend opens Razorpay checkout
# Step 4: Frontend calls /payments/verify
# Step 5: Payment service updates booking status to CONFIRMED
```

## Convenience Fee Configuration

### Set up default fees via API:

```bash
# Credit Card: 2% (min ₹10, max ₹500)
POST /payments/admin/convenience-fees
{
    "payment_method": "credit_card",
    "fee_type": "percentage",
    "fee_value": 2.0,
    "min_fee": 10.0,
    "max_fee": 500.0,
    "description": "Credit card processing fee"
}

# Debit Card: 1.5%
POST /payments/admin/convenience-fees
{
    "payment_method": "debit_card",
    "fee_type": "percentage",
    "fee_value": 1.5,
    "min_fee": 10.0,
    "max_fee": 300.0,
    "description": "Debit card processing fee"
}

# UPI: Fixed ₹10
POST /payments/admin/convenience-fees
{
    "payment_method": "upi",
    "fee_type": "fixed",
    "fee_value": 10.0,
    "min_fee": 10.0,
    "description": "UPI transaction fee"
}

# Net Banking: Fixed ₹15
POST /payments/admin/convenience-fees
{
    "payment_method": "netbanking",
    "fee_type": "fixed",
    "fee_value": 15.0,
    "min_fee": 15.0,
    "description": "Net banking fee"
}
```

## Refund Processing

### Admin initiates refund:

```bash
POST /payments/refund
{
    "transaction_id": 123,
    "amount": 5000.0,  # or null for full refund
    "reason": "Flight cancelled by airline"
}
```

This will:
1. Call Razorpay refund API
2. Update transaction status
3. Update booking status to REFUNDED
4. Credit amount to customer's original payment method

## Testing

### Test Mode Credentials
Use test credentials from Razorpay Dashboard:
- Test Key ID: `rzp_test_XXXXXXXXXX`
- Test Key Secret: `test_secret_XXXXXXXXXX`

### Test Cards
- **Success**: 4111 1111 1111 1111
- **Failure**: 4000 0000 0000 0002

### Test UPI IDs
- **Success**: success@razorpay
- **Failure**: failure@razorpay

## Security Checklist

- ✅ **Signature Verification**: All payments verified with HMAC SHA256
- ✅ **Webhook Signature**: All webhooks verified before processing
- ✅ **HTTPS Only**: Payment endpoints should use HTTPS in production
- ✅ **Idempotency**: Webhook events logged to prevent duplicate processing
- ✅ **Amount Validation**: Order amount verified before payment confirmation
- ✅ **User Authorization**: Users can only view their own transactions

## Monitoring

### Check Payment Status
```bash
# Get transaction details
GET /payments/transactions/{transaction_id}

# List user transactions
GET /payments/transactions?skip=0&limit=50
```

### Check Webhook Logs
```sql
-- View recent webhook events
SELECT * FROM webhook_logs 
ORDER BY created_at DESC 
LIMIT 50;

-- Check unprocessed webhooks
SELECT * FROM webhook_logs 
WHERE is_verified = true 
AND is_processed = false;
```

### Check Failed Payments
```sql
-- View failed payments
SELECT * FROM payment_transactions 
WHERE status = 'failed' 
ORDER BY created_at DESC;
```

## Troubleshooting

### Payment Not Confirmed After Success
**Issue**: User paid but booking still PENDING

**Check**:
1. Verify webhook is configured correctly
2. Check webhook logs table
3. Verify signature verification is passing
4. Check if Razorpay IP is whitelisted (if applicable)

### Convenience Fee Not Applied
**Issue**: Fee not calculated correctly

**Check**:
1. Verify convenience_fees table has entries
2. Check payment_method matches exactly
3. Verify is_active = true for the fee config

### Refund Failed
**Issue**: Refund API call failed

**Check**:
1. Verify payment_id exists
2. Check payment status is 'captured'
3. Verify refund amount <= original amount
4. Check Razorpay API credentials

## Production Deployment

### Before Going Live:

1. ✅ **Switch to Live Credentials**
   ```env
   RAZORPAY_KEY_ID=rzp_live_XXXXXXXXXX
   RAZORPAY_KEY_SECRET=live_secret_XXXXXXXXXX
   ```

2. ✅ **Configure Production Webhook**
   - Use production URL: `https://yourdomain.com/payments/webhook`

3. ✅ **Test with Small Amount**
   - Make test booking with ₹10
   - Verify full flow end-to-end

4. ✅ **Enable Webhooks**
   - Verify webhook events are being received
   - Check webhook logs for errors

5. ✅ **Monitor Logs**
   - Set up error alerting
   - Monitor failed payments
   - Track refund requests

## Support

For Razorpay integration issues:
- Dashboard: https://dashboard.razorpay.com
- Documentation: https://razorpay.com/docs/
- Support: support@razorpay.com
