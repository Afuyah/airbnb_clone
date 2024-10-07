from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing, Booking
from app import db
import logging
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)

agents_bp = Blueprint('agents', __name__)



@agents_bp.route('/dashboard')
@login_required
def dashboard():
    """Agent dashboard to view statistics and listings."""
    try:
        total_bookings = Booking.query.filter_by(user_id=current_user.id).count()
        total_listings = Listing.query.filter_by(agent_id=current_user.id).count()
        active_bookings = Booking.query.filter_by(user_id=current_user.id, status='Active').count()
        completed_bookings = Booking.query.filter_by(user_id=current_user.id, status='Completed').count()
        
        # Fetch listings for display
        listings = Listing.query.filter_by(agent_id=current_user.id).all()

        return render_template('agents/dashboard.html', total_bookings=total_bookings,
                               total_listings=total_listings, active_bookings=active_bookings,
                               completed_bookings=completed_bookings, listings=listings)
    except Exception as e:
        logging.error(f"Error retrieving dashboard data: {str(e)}")
        flash('Error retrieving dashboard data. Please try again later.', 'danger')
        return redirect(url_for('agents.view_listings'))  # Redirect to the listings page



# Route for viewing all listings
@agents_bp.route('/listings')
@login_required
def view_listings():
    """View all listings available to the agent."""
    try:
        listings = Listing.query.all()  # Fetch all listings
        return render_template('agents/listings.html', listings=listings)
    except Exception as e:
        logging.error(f"Error retrieving listings: {str(e)}")
        flash('Error retrieving listings. Please try again later.', 'danger')
        return redirect(url_for('agents.dashboard'))  # Redirect to a suitable page

# Route for viewing individual booking details
@agents_bp.route('/view_booking/<int:booking_id>')
@login_required
def view_booking(booking_id):
    """View details of a specific booking."""
    try:
        booking = Booking.query.get_or_404(booking_id)  # Get booking by ID
        return render_template('agents/view_booking.html', booking=booking)
    except Exception as e:
        logging.error(f"Error retrieving booking details: {str(e)}")
        flash('Error retrieving booking details. Please try again later.', 'danger')
        return redirect(url_for('agents.view_listings'))  # Redirect to the listings page

# Route for creating a new booking
@agents_bp.route('/create_booking/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def create_booking(listing_id):
    """Create a new booking for a specified listing."""
    if request.method == 'POST':
        # Validate form data
        check_in_date = request.form.get('check_in_date')
        check_out_date = request.form.get('check_out_date')
        guests = request.form.get('guests')

        # Perform necessary validations (e.g., date format, availability check)
        if datetime.strptime(check_in_date, '%Y-%m-%d') >= datetime.strptime(check_out_date, '%Y-%m-%d'):
            flash('Check-in date must be before check-out date.', 'danger')
            return redirect(url_for('agents.create_booking', listing_id=listing_id))

        # Create and save new booking
        new_booking = Booking(
            listing_id=listing_id,
            user_id=current_user.id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guests=guests,
            status='Pending'  # Default status
        )

        try:
            db.session.add(new_booking)
            db.session.commit()
            flash('Booking created successfully!', 'success')
            return redirect(url_for('agents.view_listings'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating booking: {str(e)}")
            flash('Error creating booking. Please try again.', 'danger')
            return redirect(url_for('agents.view_listings'))

    # Render the booking form for GET requests
    return render_template('agents/create_booking.html', listing_id=listing_id)

# Route for deleting a booking
@agents_bp.route('/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    """Delete a specific booking."""
    booking = Booking.query.get_or_404(booking_id)

    try:
        db.session.delete(booking)
        db.session.commit()
        flash('Booking deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting booking: {str(e)}")
        flash('Error deleting booking. Please try again.', 'danger')

    return redirect(url_for('agents.view_listings'))  # Redirect back to listings

