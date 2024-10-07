from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing, Booking, Location, Image,Amenity
from app.forms.forms import ListingForm
from app import db
from datetime import datetime

owners_bp = Blueprint('owners', __name__)

# Redirect to dashboard for the main route
@owners_bp.route('/')
@login_required
def redirect_to_dashboard():
    return redirect(url_for('owners.dashboard'))

@owners_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Count listings owned by the current user (owner)
    listings_count = Listing.query.filter_by(owner_id=current_user.id).count()

    # Fetch all listings owned by the current user
    owner_listings = Listing.query.filter_by(owner_id=current_user.id).all()

    # Get the ids of the listings
    listing_ids = [listing.id for listing in owner_listings]

    # Count the bookings tied to those listings
    bookings_count = Booking.query.filter(Booking.listing_id.in_(listing_ids)).count()

    # Get recent listings for display
    recent_listings = Listing.query.filter_by(owner_id=current_user.id).order_by(Listing.created_at.desc()).limit(5).all()

    return render_template('owners/dashboard.html', listings_count=listings_count, bookings_count=bookings_count, recent_listings=recent_listings)


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

    # Store recent listings
    recent_listings = Listing.query.filter_by(owner_id=current_user.id).order_by(Listing.created_at.desc()).limit(5).all()
    current_listing_id = recent_listings[0].id if recent_listings else None  # Ensure it gets a value or None

    if form.validate_on_submit():
        existing_listing = Listing.query.filter_by(title=form.title.data, owner_id=current_user.id).first()
        if existing_listing:
            flash('You already have a listing with that title.', 'danger')
            return render_template('owners/create_listing.html', form=form, current_listing=current_listing)

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
            db.session.rollback()
            flash('An error occurred while creating the listing. Please try again.', 'danger')
            print(f"Error: {e}")  # Log the error for debugging purposes

    return render_template('owners/create_listing.html', form=form, current_listing_id=current_listing_id)

@owners_bp.route('/edit_listing/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # Ensure the current user owns the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to edit this listing.', 'danger')
        return redirect(url_for('owners.my_listings'))

    form = ListingForm(obj=listing)  # Populate the form with existing listing data

    if form.validate_on_submit():
        listing.title = form.title.data
        listing.description = form.description.data
        listing.price = form.price.data
        listing.bedrooms = form.bedrooms.data
        listing.location_id = form.location_id.data
        
        try:
            db.session.commit()
            flash('Listing updated successfully!', 'success')
            return redirect(url_for('owners.my_listings'))
        except Exception as e:
            db.session.rollback()  # Roll back the session in case of an error
            flash('An error occurred while updating the listing. Please try again.', 'danger')
            print(f"Error: {e}")  # Log the error for debugging purposes

    return render_template('owners/edit_listing.html', form=form, listing=listing)



@owners_bp.route('/delete_listing/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # Ensure the current user owns the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to delete this listing.', 'danger')
        return redirect(url_for('owners.my_listings'))

    try:
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Roll back the session in case of an error
        flash('An error occurred while deleting the listing. Please try again.', 'danger')
        print(f"Error: {e}")  # Log the error for debugging purposes

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
        db.session.rollback()
        flash('An error occurred while deleting the image. Please try again.', 'danger')
        print(f"Error: {e}")

    return redirect(url_for('owners.view_images', listing_id=image.listing_id))

@owners_bp.route('/view_bookings/<int:listing_id>', methods=['GET'])
@login_required
def view_bookings(listing_id):
    listing = Listing.query.get_or_404(listing_id)

    # Check if the current user is the owner of the listing
    if listing.owner_id != current_user.id:
        flash('You do not have permission to view these bookings.', 'danger')
        return redirect(url_for('owners.my_listings'))

    # Get the page number from the query parameters, defaulting to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of bookings to display per page
    
    # Retrieve bookings with pagination
    bookings = Booking.query.filter_by(listing_id=listing_id).paginate(page=page, per_page=per_page, error_out=False)

    # Flash a message if no bookings are found
    if bookings.total == 0:
        flash('No bookings found for this listing.', 'info')

    return render_template('owners/view_bookings.html', 
                           bookings=bookings.items, 
                           listing=listing, 
                           pagination=bookings)


@owners_bp.route('/my_bookings')
@login_required
def my_bookings():
    # Get all listings for the current owner
    listings = Listing.query.filter_by(owner_id=current_user.id).all()
    
    # Get all active bookings for the current owner's listings
    active_bookings = Booking.query.filter(
        Booking.listing_id.in_([listing.id for listing in listings]),
        Booking.check_out_date >= datetime.utcnow() 
    ).all()

    booking_summary = []
    for booking in active_bookings:
        listing = Listing.query.get(booking.listing_id)
        booking_info = {
            'booking_id': booking.id,
            'listing_title': listing.title,
            'check_in_date': booking.check_in_date,  # Add check_in_date
            'check_out_date': booking.check_out_date,
            'num_days': (booking.check_out_date - booking.check_in_date).days,
            'status': booking.status
        }
        booking_summary.append(booking_info)

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



