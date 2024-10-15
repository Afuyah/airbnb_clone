from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.models import Listing, Location
from app import db
import logging

# Create the blueprint for the main routes
main_bp = Blueprint('main', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Route for the homepage
@main_bp.route('/')
def index():
    # Fetch page number and number of items per page from the query string
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    search_query = request.args.get('search', '', type=str)
    location_id = request.args.get('location_id', type=int)  # Get selected location from query

    # Sanitize per_page value
    per_page = min(max(per_page, 1), 100)

    try:
        # Query locations for the dropdown
        locations = Location.query.all()

        # Query listings with optional search filter and location filter
        query = Listing.query

        # Filter listings based on the search query if provided
        if search_query:
            query = query.filter(Listing.title.ilike(f'%{search_query}%'))

        # Filter by selected location if provided
        if location_id:
            query = query.filter(Listing.location_id == location_id)

        # Fetch listings and paginate the results
        featured_listings = query.paginate(page=page, per_page=per_page, error_out=False)

        if featured_listings.total == 0:
            flash("No listings found matching your criteria.", "info")

        # Render the index template with listings and pagination controls
        return render_template(
            'index.html',
            featured_listings=featured_listings.items,
            pagination=featured_listings,
            search_query=search_query,
            locations=locations,  # Pass locations for the dropdown
            selected_location_id=location_id  # Keep track of selected location
        )

    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
        flash("An error occurred while fetching listings. Please try again later.", "danger")
        return render_template('index.html', featured_listings=[], search_query=search_query, locations=[], selected_location_id=location_id)

# New route for fetching listings based on location
@main_bp.route('/listings/<int:location_id>', methods=['GET'])
def fetch_listings_by_location(location_id):
    """Fetch listings based on the selected location."""
    try:
        listings = Listing.query.filter_by(location_id=location_id).all()
        if not listings:
            return jsonify({'listings': []}), 404  # Return 404 if no listings found

        # Include images in the response
        listings_data = []
        for listing in listings:
            image_url = listing.images[0].url if listing.images else url_for('static', filename='images/placeholder.jpg')  # Use a placeholder if no image
            listings_data.append({
                'id': listing.id,
                'title': listing.title,
                'image_url': image_url,
                'price_per_night': listing.price_per_night,
                'location_name': listing.location.name,  # Ensure location name is accessible
            })
        
        return jsonify({'listings': listings_data})
    except Exception as e:
        logger.error(f"Error fetching listings by location: {e}")
        return jsonify({'error': 'An error occurred while fetching listings.'}), 500
