from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.models import Booking, Listing
from app.forms.forms import BookingForm
from app import db

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/book/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def book_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    form = BookingForm()

    if form.validate_on_submit():
        check_in = form.check_in_date.data
        check_out = form.check_out_date.data

        # Check for valid dates
        if not check_in or not check_out:
            flash('Please select both check-in and check-out dates.', 'danger')
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

        # Create new booking if no overlaps
        new_booking = Booking(
            user_id=current_user.id,
            listing_id=listing.id,
            check_in_date=check_in,
            check_out_date=check_out,
            guests=form.guests.data
        )
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking confirmed!', 'success')
        return redirect(url_for('bookings.my_bookings'))

    # On GET request or if form is not valid, check for booked status
    booked_status = False

    # Ensure the fields are properly populated
    if form.check_in_date.data and form.check_out_date.data:
        # Check if the listing is already booked during the requested period
        booked_status = Booking.query.filter(
            Booking.listing_id == listing.id,
            Booking.status != 'canceled',
            (Booking.check_in_date < form.check_out_date.data) & (Booking.check_out_date > form.check_in_date.data)
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
