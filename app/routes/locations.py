from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import Location
from app import db
from app.forms.forms import LocationForm
from flask_login import login_required

locations_bp = Blueprint('locations', __name__)

# Create (Add Location)
@locations_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_location():
    form = LocationForm()
    if form.validate_on_submit():
        new_location = Location(
            name=form.name.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data
        )
        db.session.add(new_location)
        db.session.commit()
        flash('Location added successfully!', 'success')
        return redirect(url_for('locations.view_locations'))
    
    return render_template('locations/add_location.html', form=form)

# Read (View all locations)
@locations_bp.route('/')
def view_locations():
    locations = Location.query.all()
    return render_template('locations/view_locations.html', locations=locations)

# Update (Edit a location)
@locations_bp.route('/edit/<int:location_id>', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)  # Pre-fill the form with existing data
    if form.validate_on_submit():
        location.name = form.name.data
        location.latitude = form.latitude.data
        location.longitude = form.longitude.data
        db.session.commit()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('locations.view_locations'))
    
    return render_template('locations/edit_location.html', form=form, location=location)


@locations_bp.route('/delete/<int:location_id>', methods=['POST'])
@login_required
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted successfully!', 'success')
    return redirect(url_for('locations.view_locations'))
