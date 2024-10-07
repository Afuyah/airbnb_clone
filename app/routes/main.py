from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing, Amenity, Image, Location
from app.forms.forms import ListingForm, BookingForm
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Fetch featured listings, you can modify the query as needed
    featured_listings = Listing.query.limit(6).all()  # Fetch the first 6 listings as featured
    return render_template('index.html', featured_listings=featured_listings)
