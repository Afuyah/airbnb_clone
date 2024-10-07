from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.models import User, Listing, Booking, SupportRequest, Amenity
from app import db
from app.forms.forms import AmenityForm, SupportRequestForm  # Assuming these forms are defined

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def dashboard():
    users = User.query.all()
    listings = Listing.query.all()
    bookings = Booking.query.all()
    return render_template('admin/dashboard.html', users=users, listings=listings, bookings=bookings)

# User Management
@admin_bp.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Check if the user has bookings or listings before deletion
    if Booking.query.filter_by(user_id=user.id).count() > 0 or Listing.query.filter_by(owner_id=user.id).count() > 0:
        flash('Cannot delete user with associated bookings or listings.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

# Booking Management
@admin_bp.route('/bookings')
@login_required
def manage_bookings():
    bookings = Booking.query.all()
    return render_template('admin/manage_bookings.html', bookings=bookings)

@admin_bp.route('/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking deleted successfully!', 'success')
    return redirect(url_for('admin.manage_bookings'))

# Listing Management
@admin_bp.route('/listings')
@login_required
def manage_listings():
    listings = Listing.query.all()
    return render_template('admin/manage_listings.html', listings=listings)

@admin_bp.route('/listings/delete/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('admin.manage_listings'))

# Support Request Management
@admin_bp.route('/support_requests')
@login_required
def manage_support_requests():
    requests = SupportRequest.query.all()
    return render_template('admin/manage_support_requests.html', requests=requests)

@admin_bp.route('/support_request/<int:request_id>/update', methods=['POST'])
@login_required
def update_support_request(request_id):
    support_request = SupportRequest.query.get_or_404(request_id)
    status = request.form.get('status')

    if status:
        support_request.status = status
        db.session.commit()
        flash('Support request updated successfully.', 'success')
    else:
        flash('Status is required.', 'danger')

    return redirect(url_for('admin.manage_support_requests'))

@admin_bp.route('/support_request/<int:request_id>/delete', methods=['POST'])
@login_required
def delete_support_request(request_id):
    support_request = SupportRequest.query.get_or_404(request_id)
    db.session.delete(support_request)
    db.session.commit()
    flash('Support request deleted successfully.', 'success')
    return redirect(url_for('admin.manage_support_requests'))

@admin_bp.route('/amenities')
@login_required
def manage_amenities():
    amenities = Amenity.query.all()
    return render_template('admin/manage_amenities.html', amenities=amenities)

@admin_bp.route('/add_amenity', methods=['POST'])
def add_amenity():
    name = request.form.get('name')
    if not name:
        flash('Amenity name is required.', 'error')
        return redirect(url_for('admin.manage_amenities'))  # Redirect back to the amenities management page

    # Add logic to save the amenity to the database
    new_amenity = Amenity(name=name)
    db.session.add(new_amenity)
    db.session.commit()
    flash('Amenity added successfully!', 'success')
    return redirect(url_for('admin.manage_amenities'))

@admin_bp.route('/delete_amenity/<int:amenity_id>', methods=['POST'])
@login_required
def delete_amenity(amenity_id):
    amenity = Amenity.query.get_or_404(amenity_id)
    db.session.delete(amenity)
    db.session.commit()
    flash('Amenity deleted successfully.', 'success')
    return redirect(url_for('admin.manage_amenities'))