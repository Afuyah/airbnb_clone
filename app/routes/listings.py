from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing, Amenity, Image, Location, listing_amenities,Booking
from app.forms.forms import ListingForm, BookingForm
from app import db
import os
from werkzeug.utils import secure_filename

listings_bp = Blueprint('listings', __name__)

# Directory to save images
UPLOAD_FOLDER = 'app/static/upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and filename != ''

def save_image(image):
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Ensure the upload folder exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        try:
            image.save(image_path)
            return f'/static/upload/{filename}'  # Return URL for accessing the image
        except Exception as e:
            flash(f'Error saving image: {str(e)}', 'danger')  # Flash error message
            return None
    return None

@listings_bp.route('/listings', methods=['GET'])
def list_listings():
    # Fetch all listings with their associated data
    listings = (
        db.session.query(Listing)
        .outerjoin(Location)  # Join with the Location table
        .outerjoin(Image)     # Join with the Image table
        .outerjoin(listing_amenities)  # Join with the association table
        .outerjoin(Amenity)   # Join with the Amenity table
        .options(
            db.orm.subqueryload(Listing.amenities),
            db.orm.subqueryload(Listing.images),
            db.orm.subqueryload(Listing.location)  # Correct usage
        )

        .all() 
    )

    return render_template('listings/view_listings.html', listings=listings)

@listings_bp.route('/view/<int:listing_id>', methods=['GET'])
def view_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    related_listings = Listing.query.filter_by(location_id=listing.location_id).limit(3).all()  # Get related listings
    booking_form = BookingForm()  # Create a new booking form instance
    return render_template('listings/view_listing.html', listing=listing, related_listings=related_listings, booking_form=booking_form)

@listings_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = ListingForm()
    
    if form.validate_on_submit():
        new_listing = Listing(
            title=form.title.data,
            description=form.description.data,
            price_per_night=form.price.data,
            owner_id=current_user.id,
            location_id=form.location_id.data
        )
        db.session.add(new_listing)

        # Commit to save the listing first and generate its ID for the image association
        db.session.commit()

        selected_amenities = form.amenities.data
        for amenity_id in selected_amenities:
            amenity = Amenity.query.get(amenity_id)
            if amenity:
                new_listing.amenities.append(amenity)

        images = request.files.getlist('images')
        for image_file in images:
            if image_file and allowed_file(image_file.filename):
                image_url = save_image(image_file)
                if image_url:
                    new_image = Image(url=image_url, listing_id=new_listing.id)
                    db.session.add(new_image)

        try:
            db.session.commit()
            flash('Listing created successfully.', 'success')
            return redirect(url_for('listings.view_listing', listing_id=new_listing.id))
        except Exception as e:
            db.session.rollback()  # Rollback the session if there is an error
            flash(f'Error creating listing: {str(e)}', 'danger')

    return render_template('listings/create_listing.html', form=form)
@listings_bp.route('/search', methods=['GET'])
def search():
    location = request.args.get('location')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    # Start with all listings
    query = Listing.query

    # Filter by location
    if location:
        query = query.filter(Listing.location.has(name=location))

    # Filter out listings that are booked during the selected dates
    if check_in and check_out:
        booked_listings = (
            db.session.query(Booking.listing_id)
            .filter(
                Booking.check_in_date < check_out,
                Booking.check_out_date > check_in
            )
            .subquery()
        )

        query = query.filter(Listing.id.notin_(booked_listings))

    listings = query.all()  # Execute the query

    return render_template('listings/search_results.html', listings=listings, location=location, check_in=check_in, check_out=check_out)