from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing, Booking, Location, Image, Amenity
from app.forms.forms import ListingForm
from app import db
from datetime import datetime
import logging

owners_bp = Blueprint('owners', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Error handling helper function
def handle_db_error(e, operation):
    db.session.rollback()
    flash(f'An error occurred while {operation}. Please try again.', 'danger')
    logging.error(f"Database Error: {e}")  # Log the error for debugging

# Owner check decorator
def owner_required(func):
    def wrapper(*args, **kwargs):
        listing = Listing.query.get_or_404(kwargs['listing_id'])
        if listing.owner_id != current_user.id:
            flash('You do not have permission to access this listing.', 'danger')
            return redirect(url_for('owners.my_listings'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__  # Preserve the original function name
    return wrapper

# Redirect to dashboard for the main route
@owners_bp.route('/')
@login_required
def redirect_to_dashboard():
    return redirect(url_for('owners.dashboard'))

@owners_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    owner_listings = Listing.query.filter_by(owner_id=current_user.id).all()
    listing_ids = [listing.id for listing in owner_listings]
    bookings_count = Booking.query.filter(Booking.listing_id.in_(listing_ids)).count()
    recent_listings = Listing.query.filter_by(owner_id=current_user.id).order_by(Listing.created_at.desc()).limit(5).all()

    return render_template('owners/dashboard.html', 
                           listings_count=len(owner_listings), 
                           bookings_count=bookings_count, 
                           recent_listings=recent_listings)

# View all listings belonging to the current owner
@owners_bp.route('/my_listings')
@login_required
def my_listings():
    listings = Listing.query.filter_by(owner_id=current_user.id).all()
    amenities = Amenity.query.all()  # Fetch all amenities from the database
    return render_template('owners/my_listings.html', listings=listings, amenities=amenities)

# Create a new listing
@owners_bp.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = ListingForm()
    form.location_id.choices = [(location.id, location.name) for location in Location.query.all()]
    
    if form.validate_on_submit():
        existing_listing = Listing.query.filter_by(title=form.title.data, owner_id=current_user.id).first()
        if existing_listing:
            flash('You already have a listing with that title.', 'danger')
            return render_template('owners/create_listing.html', form=form)

        try:
            new_listing = Listing(
                title=form.title.data,
                description=form.description.data,
                price_per_night=form.price_per_night.data,
                bedrooms=form.bedrooms.data,
                owner_id=current_user.id,
                location_id=form.location_id.data
            )
            db.session.add(new_listing)
            db.session.commit()
            flash('Listing created successfully!', 'success')
            return redirect(url_for('owners.my_listings'))

        except Exception as e:
            handle_db_error(e, "creating the listing")

    return render_template('owners/create_listing.html', form=form)

@owners_bp.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
@login_required
@owner_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    form = ListingForm(obj=listing)  # Populate the form with existing listing data
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]

    if form.validate_on_submit():
        form.populate_obj(listing)  # Simplifies updating the listing fields

        try:
            db.session.commit()
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('owners.my_listings'))
        except Exception as e:
            handle_db_error(e, "updating the listing")

    return render_template('owners/edit_listing.html', form=form, listing=listing)

@owners_bp.route('/delete_listing/<int:listing_id>', methods=['POST'])
@login_required
@owner_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    try:
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted successfully!', 'success')
    except Exception as e:
        handle_db_error(e, "deleting the listing")

    return redirect(url_for('owners.my_listings'))

# Delete an image associated with a listing
@owners_bp.route('/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)

    if image.listing.owner_id != current_user.id:
        flash('You do not have permission to delete this image.', 'danger')
        return redirect(url_for('owners.my_listings'))

    try:
        db.session.delete(image)
        db.session.commit()
        flash('Image deleted successfully!', 'success')
    except Exception as e:
        handle_db_error(e, "deleting the image")

    return redirect(url_for('owners.view_images', listing_id=image.listing_id))

@owners_bp.route('/view_bookings/<int:listing_id>', methods=['GET'])
@login_required
@owner_required
def view_bookings(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of bookings to display

    bookings = Booking.query.filter_by(listing_id=listing_id).paginate(page=page, per_page=per_page, error_out=False)

    if bookings.total == 0:
        flash('No bookings found for this listing.', 'info')

    return render_template('owners/view_bookings.html', bookings=bookings.items, listing=listing, pagination=bookings)

@owners_bp.route('/my_bookings')
@login_required
def my_bookings():
    listings = Listing.query.filter_by(owner_id=current_user.id).all()
    active_bookings = Booking.query.filter(
        Booking.listing_id.in_([listing.id for listing in listings]),
        Booking.check_out_date >= datetime.utcnow()
    ).all()

    booking_summary = [{
        'booking_id': booking.id,
        'listing_title': Listing.query.get(booking.listing_id).title,
        'check_in_date': booking.check_in_date,
        'check_out_date': booking.check_out_date,
        'num_days': (booking.check_out_date - booking.check_in_date).days,
        'status': booking.status
    } for booking in active_bookings]

    return render_template('owners/my_bookings.html', bookings=booking_summary)

@owners_bp.route('/booking_details/<int:booking_id>')
@login_required
def booking_details(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    listing = Listing.query.get(booking.listing_id)

    # Ensure the current user is the owner of the listing
    if listing.owner_id != current_user.id:
        return "You do not have access to this booking", 403

    booking_info = {
        'booking_id': booking.id,
        'listing_title': listing.title,
        'user': booking.user.username,
        'check_in_date': booking.check_in_date,
        'check_out_date': booking.check_out_date,
        'num_days': (booking.check_out_date - booking.check_in_date).days,
        'guests': booking.guests,
        'status': booking.status,
        'created_at': booking.created_at
    }

    return render_template('owners/booking_details.html', booking=booking_info)

# Approve a booking
@owners_bp.route('/approve_booking/<int:booking_id>', methods=['POST'])
@login_required
def approve_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    listing = Listing.query.get(booking.listing_id)

    # Ensure the current user is the owner of the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to approve this booking.', 'danger')
        return redirect(url_for('owners.my_bookings'))

    try:
        booking.status = 'approved'  # Set the booking status to approved
        db.session.commit()
        flash('Booking approved successfully!', 'success')
    except Exception as e:
        handle_db_error(e, "approving the booking")

    return redirect(url_for('owners.my_bookings'))

# Reject a booking
@owners_bp.route('/reject_booking/<int:booking_id>', methods=['POST'])
@login_required
def reject_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    listing = Listing.query.get(booking.listing_id)

    # Ensure the current user is the owner of the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to reject this booking.', 'danger')
        return redirect(url_for('owners.my_bookings'))

    try:
        booking.status = 'rejected'  # Set the booking status to rejected
        db.session.commit()
        flash('Booking rejected successfully!', 'success')
    except Exception as e:
        handle_db_error(e, "rejecting the booking")

    return redirect(url_for('owners.my_bookings'))

@owners_bp.route('/tag_amenities/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def tag_amenities(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # Ensure the current user owns the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to tag amenities to this listing.', 'danger')
        return redirect(url_for('owners.my_listings'))

    # Fetch all available amenities from the database
    available_amenities = Amenity.query.all()
    
    # Get the amenities already tagged to the listing
    current_amenities = [amenity.id for amenity in listing.amenities]

    if request.method == 'POST':
        selected_amenities = request.form.getlist('amenities')  # Get selected amenities from the form

        try:
            # Clear current amenities for the listing
            listing.amenities.clear()

            # Add selected amenities
            for amenity_id in selected_amenities:
                amenity = Amenity.query.get(amenity_id)
                if amenity:
                    listing.amenities.append(amenity)

            db.session.commit()
            flash('Amenities tagged successfully!', 'success')
            return redirect(url_for('owners.my_listings'))

        except Exception as e:
            handle_db_error(e, "tagging amenities")

    return render_template('owners/tag_amenities.html', 
                           listing=listing, 
                           available_amenities=available_amenities, 
                           current_amenities=current_amenities)
