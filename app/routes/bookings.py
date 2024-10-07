from flask import Blueprint, render_template, redirect, url_for, flash
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
        new_booking = Booking(
            user_id=current_user.id,
            listing_id=listing.id,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            guests=form.guests.data  # Make sure to include this line
        )
        db.session.add(new_booking)
        db.session.commit()
        flash('Booking confirmed!', 'success')
        return redirect(url_for('bookings.my_bookings'))
    return render_template('bookings/book_listing.html', form=form, listing=listing)



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
