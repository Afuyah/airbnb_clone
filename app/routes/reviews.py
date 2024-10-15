from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.models import Review, Listing, Booking
from app.forms.forms import ReviewForm
from app import db
from datetime import datetime, timedelta

reviews_bp = Blueprint('reviews', __name__)

def has_booked_listing(listing_id, user_id):
    # Check for completed bookings within the last 30 days
    completed_booking = Booking.query.filter_by(
        listing_id=listing_id,
        user_id=user_id,
        status='completed'
    ).first()
    return completed_booking and completed_booking.created_at >= datetime.utcnow() - timedelta(days=30)

def validate_review_content(content):
    # Define prohibited words
    prohibited_words = ['offensive_word1', 'offensive_word2']  # Add real offensive words
    for word in prohibited_words:
        if word in content.lower():
            return False
    return True

# Add or edit a review for a specific listing
@reviews_bp.route('/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def add_or_edit_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    listing = Listing.query.get_or_404(booking.listing_id)
    form = ReviewForm()

    # Check if the user has booked the listing
    if booking.user_id != current_user.id:
        flash('You are not authorized to review this listing.', 'danger')
        return redirect(url_for('bookings.view_bookings'))

    # Check if the user has already reviewed this listing
    existing_review = Review.query.filter_by(listing_id=listing.id, user_id=current_user.id).first()

    if existing_review:
        # If the review exists, populate the form with existing review data for editing
        if form.validate_on_submit():
            if not validate_review_content(form.content.data):
                flash('Your review contains inappropriate content and cannot be submitted.', 'danger')
                return redirect(url_for('bookings.view_bookings'))

            existing_review.content = form.content.data
            existing_review.rating = form.rating.data
            db.session.commit()
            flash('Review updated!', 'success')
            return redirect(url_for('listings.view_listing', listing_id=listing.id))
        else:
            # Pre-fill the form with existing review data
            form.content.data = existing_review.content
            form.rating.data = existing_review.rating
    else:
        # If no review exists, handle new review submission
        if form.validate_on_submit():
            if not validate_review_content(form.content.data):
                flash('Your review contains inappropriate content and cannot be submitted.', 'danger')
                return redirect(url_for('bookings.view_bookings'))

            new_review = Review(
                listing_id=listing.id,
                user_id=current_user.id,
                content=form.content.data,
                rating=form.rating.data
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Review submitted! It will be visible once approved.', 'success')
            return redirect(url_for('listings.view_listing', listing_id=listing.id))

    return render_template('reviews/add_edit_review.html', form=form, listing=listing)

# View all approved reviews for a specific listing
@reviews_bp.route('/<int:listing_id>')
def view_reviews(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    reviews = Review.query.filter_by(listing_id=listing.id, is_approved=True).all()
    return render_template('reviews/view_reviews.html', listing=listing, reviews=reviews)
