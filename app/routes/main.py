from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import Listing
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    try:
        # Correctly using paginate method
        featured_listings = Listing.query.paginate(page=page, per_page=per_page, error_out=False)
        return render_template('index.html', featured_listings=featured_listings.items, pagination=featured_listings)
    except Exception as e:
        flash("An error occurred while fetching listings. Please try again later.", "danger")
        return render_template('index.html', featured_listings=[])
