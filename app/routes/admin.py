from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, make_response
from flask_login import login_required, current_user
from app.models.models import User, Listing, Booking, SupportRequest, Amenity, AuditLog
from app import db
from datetime import datetime, timedelta
import csv
from io import StringIO
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role != role and current_user.role != 'super_admin':
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return wrapper


def log_action(action):
    log = AuditLog(action=action, user_id=current_user.id, timestamp=datetime.utcnow())
    db.session.add(log)
    db.session.commit()


@admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    users = User.query.all()
    listings = Listing.query.all()
    bookings = Booking.query.all()

    # Analytics
    today = datetime.utcnow().date()
    labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    data = [User.query.filter(User.created_at.between(today - timedelta(days=i+1), today - timedelta(days=i))).count() for i in range(7)]

    # Recent activities
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    pending_support_requests = SupportRequest.query.filter_by(status='Pending').count()

    return render_template('admin/dashboard.html', users=users, listings=listings, bookings=bookings, labels=labels, data=data, recent_bookings=recent_bookings, pending_support_requests=pending_support_requests)


@admin_bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    search_query = request.args.get('search')
    if search_query:
        users = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
    else:
        users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if Booking.query.filter_by(user_id=user.id).count() > 0 or Listing.query.filter_by(owner_id=user.id).count() > 0:
        flash('Cannot delete user with associated bookings or listings.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        log_action(f"Deleted user {user.username}")
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/export')
@login_required
@role_required('admin')
def export_users():
    users = User.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Username', 'Email', 'Role'])

    for user in users:
        writer.writerow([user.id, user.username, user.email, user.role])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=users.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@admin_bp.route('/bookings')
@login_required
@role_required('admin')
def manage_bookings():
    bookings = Booking.query.all()
    return render_template('admin/manage_bookings.html', bookings=bookings)

@admin_bp.route('/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    log_action(f"Deleted booking ID {booking_id}")
    flash('Booking deleted successfully!', 'success')
    return redirect(url_for('admin.manage_bookings'))

@admin_bp.route('/bookings/export')
@login_required
@role_required('admin')
def export_bookings():
    bookings = Booking.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'User', 'Listing', 'Check-in', 'Check-out'])

    for booking in bookings:
        writer.writerow([booking.id, booking.user.username, booking.listing.title, booking.check_in, booking.check_out])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=bookings.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@admin_bp.route('/listings')
@login_required
@role_required('admin')
def manage_listings():
    listings = Listing.query.all()
    return render_template('admin/manage_listings.html', listings=listings)

@admin_bp.route('/listings/delete/<int:listing_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    db.session.delete(listing)
    db.session.commit()
    log_action(f"Deleted listing {listing.title}")
    flash('Listing deleted successfully!', 'success')
    return redirect(url_for('admin.manage_listings'))


@admin_bp.route('/support_requests')
@login_required
@role_required('admin')
def manage_support_requests():
    requests = SupportRequest.query.all()
    return render_template('admin/manage_support_requests.html', requests=requests)

@admin_bp.route('/support_request/<int:request_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_support_request(request_id):
    support_request = SupportRequest.query.get_or_404(request_id)
    status = request.form.get('status')

    if status:
        support_request.status = status
        db.session.commit()
        log_action(f"Updated support request ID {support_request.id} to status {status}")
        send_email(
            subject="Support Request Update",
            recipient=support_request.user.email,
            body=f"Your support request has been updated to status: {status}"
        )
        flash('Support request updated successfully.', 'success')
    else:
        flash('Status is required.', 'danger')

    return redirect(url_for('admin.manage_support_requests'))

@admin_bp.route('/support_request/<int:request_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_support_request(request_id):
    support_request = SupportRequest.query.get_or_404(request_id)
    db.session.delete(support_request)
    db.session.commit()
    log_action(f"Deleted support request ID {request_id}")
    flash('Support request deleted successfully!', 'success')
    return redirect(url_for('admin.manage_support_requests'))

@admin_bp.route('/amenities')
@login_required
@role_required('admin')
def manage_amenities():
    amenities = Amenity.query.all()
    return render_template('admin/manage_amenities.html', amenities=amenities)

@admin_bp.route('/add_amenity', methods=['POST'])
@login_required
@role_required('admin')
def add_amenity():
    name = request.form.get('name')
    if not name:
        flash('Amenity name is required.', 'danger')
        return redirect(url_for('admin.manage_amenities'))

    new_amenity = Amenity(name=name)
    db.session.add(new_amenity)
    db.session.commit()
    log_action(f"Added amenity {name}")
    flash('Amenity added successfully!', 'success')
    return redirect(url_for('admin.manage_amenities'))

@admin_bp.route('/delete_amenity/<int:amenity_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_amenity(amenity_id):
    amenity = Amenity.query.get_or_404(amenity_id)
    db.session.delete(amenity)
    db.session.commit()
    log_action(f"Deleted amenity {amenity.name}")
    flash('Amenity deleted successfully!', 'success')
    return redirect(url_for('admin.manage_amenities'))

@admin_bp.route('/audit_logs')
@login_required
@role_required('admin')
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('admin/audit_logs.html', logs=logs)