from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app, render_template
from flask_login import login_required, current_user
from app.models.models import Booking, Payment
from app.forms.forms import PaymentForm
from app import db
from datetime import datetime
import logging
import requests
import hmac
import hashlib
import json
from logging.handlers import RotatingFileHandler


payments_bp = Blueprint('payments', __name__)


# Setup logger
logger = logging.getLogger('payment_logger')
logger.setLevel(logging.INFO)

# Using RotatingFileHandler for log rotation
handler = RotatingFileHandler('payment_actions.log', maxBytes=10*1024*1024, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Helper function to log actions
def log_action(action, data=None):
    try:
        logger.info(f"{datetime.utcnow()}: {action} - {json.dumps(data or {})}")
    except Exception as e:
        logger.error(f"Error logging action '{action}': {e}")

def generate_hmac_signature(secret_key, data):
    """Generate HMAC signature for outgoing requests."""
    try:
        message = json.dumps(data).encode('utf-8')
        return hmac.new(secret_key.encode(), message, hashlib.sha256).hexdigest()
    except Exception as e:
        logger.error(f"Error generating HMAC signature: {e}")
        return None  # Handle error as needed

def verify_hmac_signature(secret_key, data, provided_signature):
    """Verify the HMAC signature from incoming M-Pesa webhook responses."""
    try:
        expected_signature = generate_hmac_signature(secret_key, data)
        return hmac.compare_digest(expected_signature, provided_signature)
    except Exception as e:
        logger.error(f"Error verifying HMAC signature: {e}")
        return False  # Handle error as needed


# Route to render the payment page
@payments_bp.route('/payment/<int:booking_id>', methods=['GET'])
@login_required
def payment_page(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    total_amount = booking.total_price
    
    # Create an instance of the payment form
    form = PaymentForm()

    return render_template('payments/payments_page.html', booking=booking, total_amount=total_amount, form=form)


@payments_bp.route('/initiate_payment', methods=['POST'])
@login_required
def initiate_payment():
    booking_id = request.form.get('booking_id')
    phone_number = request.form.get('phone_number')

    # Validate inputs
    if not phone_number or not phone_number.isdigit() or len(phone_number) < 10:
        flash('Invalid phone number. Please provide a valid number.', 'danger')
        return redirect(url_for('bookings.my_bookings'))

    # Fetch the booking details
    booking = Booking.query.get_or_404(booking_id)

    # Ensure the user is paying for their own booking
    if booking.user_id != current_user.id:
        log_action('Unauthorized payment attempt', {'user_id': current_user.id, 'booking_id': booking.id})
        flash('Unauthorized payment attempt.', 'danger')
        return redirect(url_for('bookings.my_bookings'))

    total_amount = booking.total_price
    log_action('Payment initiation request', {
        'user_id': current_user.id,
        'booking_id': booking.id,
        'amount': total_amount,
        'phone_number': '***'  # Obscure phone number in logs
    })

    # Prepare the payment data (For M-Pesa or other APIs)
    payment_data = {
        "phone_number": phone_number,
        "amount": total_amount,
        "booking_id": booking_id,
        "description": f"Booking payment for {booking.listing.name}",
    }

    # Generate HMAC signature for secure request
    secret_key = current_app.config.get('MPESA_SECRET_KEY')
    signature = generate_hmac_signature(secret_key, payment_data)

    try:
        # Initiate payment via M-Pesa STK Push or another API
        response = initiate_mpesa_payment(payment_data, signature)

        if response.status_code == 200:
            log_action('M-Pesa payment initiated', response.json())

            # Log the payment details in the database
            payment = Payment(
                user_id=current_user.id,
                booking_id=booking.id,
                amount=total_amount,
                phone_number=phone_number,
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()

            flash('Payment request sent. Please complete the payment on your phone.', 'success')
            return redirect(url_for('payments.confirm_payment', payment_id=payment.id))

        else:
            log_action('Payment initiation failed', {
                'response': response.json(),
                'status_code': response.status_code
            })
            flash('Payment initiation failed. Please try again.', 'danger')
            return redirect(url_for('bookings.my_bookings'))

    except requests.exceptions.RequestException as e:
        log_action('Payment initiation error', {'error': str(e)})
        flash('An error occurred during the payment process. Please try again later.', 'danger')
        return redirect(url_for('bookings.my_bookings'))




@payments_bp.route('/confirm_payment/<int:payment_id>', methods=['GET'])
@login_required
def confirm_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)

    # Verify payment for the user who made it
    if payment.user_id != current_user.id:
        log_action('Unauthorized payment confirmation', {'user_id': current_user.id, 'payment_id': payment.id})
        flash('Unauthorized access to payment confirmation.', 'danger')
        return redirect(url_for('bookings.my_bookings'))

    log_action('Payment confirmation request', {'user_id': current_user.id, 'payment_id': payment.id})

    # Verify the payment via M-Pesa API
    try:
        verification_response = verify_mpesa_payment(payment_id)

        if verification_response['status'] == 'completed':
            # Update payment and booking status
            payment.status = 'completed'
            payment.booking.status = 'confirmed'
            db.session.commit()

            log_action('Payment completed', {'payment_id': payment.id, 'booking_id': payment.booking.id})
            flash('Payment completed successfully!', 'success')
            return redirect(url_for('bookings.my_bookings'))

        elif verification_response['status'] == 'failed':
            log_action('Payment failed', verification_response)
            flash('Payment failed. Please try again.', 'danger')
            return redirect(url_for('bookings.my_bookings'))

        else:
            log_action('Payment pending', verification_response)
            flash('Payment is still pending. Please try again later.', 'warning')
            return redirect(url_for('bookings.my_bookings'))

    except Exception as e:
        log_action('Payment verification error', {'error': str(e)})
        flash('Error verifying payment. Please contact support.', 'danger')
        return redirect(url_for('bookings.my_bookings'))




@payments_bp.route('/payment_webhook', methods=['POST'])
def payment_webhook():
    # M-Pesa will send payment updates to this endpoint
    payload = request.get_json()
    provided_signature = request.headers.get('X-MPesa-Signature')

    # Verify the HMAC signature to ensure the request is legitimate
    secret_key = current_app.config.get('MPESA_SECRET_KEY')
    if not verify_hmac_signature(secret_key, payload, provided_signature):
        log_action('Invalid webhook signature', payload)
        return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400

    # Validate the payload structure
    payment_id = payload.get('payment_id')
    status = payload.get('status')

    if not payment_id or status is None:
        log_action('Invalid payload structure', payload)
        return jsonify({'status': 'error', 'message': 'Missing payment_id or status'}), 400

    payment = Payment.query.get(payment_id)
    if not payment:
        log_action('Invalid payment ID in webhook', payload)
        return jsonify({'status': 'error', 'message': 'Payment not found'}), 404

    # Update payment status based on webhook data
    try:
        if status == 'completed':
            payment.status = 'completed'
            payment.booking.status = 'confirmed'
        elif status == 'failed':
            payment.status = 'failed'
        else:
            payment.status = 'pending'

        db.session.commit()
        log_action('Payment status updated via webhook', {'payment_id': payment_id, 'status': status})

    except Exception as e:
        log_action('Database commit error', {'error': str(e), 'payment_id': payment_id})
        return jsonify({'status': 'error', 'message': 'Failed to update payment status'}), 500

    return jsonify({'status': 'success'}), 200
