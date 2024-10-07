from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Review, Listing
from app.forms.forms import ReviewForm
from app import db

reviews_bp = Blueprint('reviews', __name__)

# Add a review for a specific listing
@reviews_bp.route('/add/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def add_review(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    form = ReviewForm()
    
    # Check if the user has already reviewed this listing
    existing_review = Review.query.filter_by(listing_id=listing.id, user_id=current_user.id).first()
    if existing_review:
        flash('You have already submitted a review for this listing.', 'warning')
        return redirect(url_for('listings.view_listing', listing_id=listing.id))
    
    if form.validate_on_submit():
        new_review = Review(
            listing_id=listing.id,
            user_id=current_user.id,
            content=form.content.data,
            rating=form.rating.data
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted!', 'success')
        return redirect(url_for('listings.view_listing', listing_id=listing.id))
    
    return render_template('reviews/add_review.html', form=form, listing=listing)

# View all reviews for a specific listing
@reviews_bp.route('/<int:listing_id>')
def view_reviews(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    reviews = Review.query.filter_by(listing_id=listing.id).all()
    return render_template('reviews/view_reviews.html', listing=listing, reviews=reviews)
