from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.models.models import Booking, Listing
from app.forms.forms import BookingForm
from app import db
from datetime import datetime

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/book/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def book_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    form = BookingForm()

    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data
        guests = form.guests.data  # Ensure to capture the guests from the form

        # Check for valid dates
        if not check_in or not check_out:
            flash('Please select both check-in and check-out dates.', 'danger')
            return redirect(url_for('bookings.book_listing', listing_id=listing_id))

        # Ensure check-in is before check-out
        if check_in >= check_out:
            flash('Check-out date must be after check-in date.', 'danger')
            return redirect(url_for('bookings.book_listing', listing_id=listing_id))

        # Check for overlapping bookings
        overlapping_bookings = Booking.query.filter(
            Booking.listing_id == listing.id,
            Booking.status != 'canceled',
            (Booking.check_in_date < check_out) & (Booking.check_out_date > check_in)
        ).first()

        if overlapping_bookings:
            flash('The selected dates are not available. Please choose different dates.', 'danger')
            return redirect(url_for('bookings.book_listing', listing_id=listing_id))

        # Calculate total price
        duration = (check_out - check_in).days
        total_price = duration * listing.price_per_night

        # Create a new booking entry
        booking = Booking(
            user_id=current_user.id,
            listing_id=listing.id,
            check_in_date=check_in,
            check_out_date=check_out,
            guests=guests,  # Assign guests value from the form
            total_price=total_price,
            status='pending'  # Status before payment
        )
        
        # Add and commit the new booking to the database
        db.session.add(booking)
        db.session.commit()

        # Redirect to the payment page with the booking ID
        return redirect(url_for('payments.payment_page', booking_id=booking.id))

    # On GET request or if form is not valid, check for booked status
    booked_status = False

    if form.check_in_date.data and form.check_out_date.data:
        # Check if the listing is already booked during the requested period
        booked_status = Booking.query.filter(
            Booking.listing_id == listing.id,
            Booking.status != 'canceled',
            (Booking.check_in_date < form.check_out_date.data) & 
            (Booking.check_out_date > form.check_in_date.data)
        ).count() > 0

    return render_template('bookings/book_listing.html', form=form, listing=listing, booked_status=booked_status)



@bookings_bp.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('bookings/my_bookings.html', bookings=bookings)


@bookings_bp.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id == current_user.id:  
        booking.status = 'canceled'
        db.session.commit()
        flash('Booking canceled.', 'success')
    else:
        flash('You do not have permission to cancel this booking.', 'danger')
    return redirect(url_for('bookings.my_bookings'))


@bookings_bp.route('/get_booked_dates/<int:listing_id>', methods=['GET'])
def get_booked_dates(listing_id):
    # Retrieve bookings for the listing
    bookings = Booking.query.filter(
        Booking.listing_id == listing_id,
        Booking.status != 'canceled'  # Exclude canceled bookings
    ).all()

    booked_dates = []
    for booking in bookings:
        booked_dates.append({
            'start': booking.check_in_date.isoformat(),
            'end': booking.check_out_date.isoformat()
        })

    return jsonify(booked_dates)


@bookings_bp.route('/check_availability/<int:listing_id>', methods=['GET'])
def check_availability(listing_id):
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    # Ensure check-in and check-out dates are provided
    if check_in and check_out:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)

        overlapping_bookings = Booking.query.filter(
            Booking.listing_id == listing_id,
            Booking.status != 'canceled',
            (Booking.check_in_date < check_out_date) & (Booking.check_out_date > check_in_date)
        ).first()

        if overlapping_bookings:
            return jsonify({'available': False})

    return jsonify({'available': True})
