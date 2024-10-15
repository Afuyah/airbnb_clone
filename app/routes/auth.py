from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import User  # Import the User model for authentication
from app.forms.forms import LoginForm, RegistrationForm  # Import forms for login and registration
import logging  # For logging errors

# Define the Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# -------------------------
# LOGIN ROUTE
# -------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])

def login():
    form = LoginForm()  # Create an instance of the login form
    if form.validate_on_submit():  # Check if form data is valid and POST request
        # Query the user by email
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):  # Verify the password
            login_user(user)  # Log the user in using Flask-Login's login_user()
            flash('Login successful!', 'success')  # Flash success message
            next_page = request.args.get('next')  # Get the 'next' page if available
            return redirect(next_page) if next_page else redirect(url_for('main.index'))  # Redirect after login
        else:
            flash('Login failed. Please check your credentials.', 'danger')  # Flash error message if login fails
    return render_template('auth/login.html', form=form)  # Render the login template

# -------------------------
# REGISTRATION ROUTE
# -------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()  # Create an instance of the registration form
    if form.validate_on_submit():  # Check if form data is valid and POST request
        # Check if the email is already registered
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please use another.', 'danger')  # Flash error if email exists
            return redirect(url_for('auth.register'))

        # Create a new user with hashed password
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)  # Hash the password

        try:
            # Add and commit the new user to the database
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')  # Flash success message
            return redirect(url_for('auth.login'))  # Redirect to the login page after successful registration
        except Exception as e:
            db.session.rollback()  # Rollback the session if there's a database error
            logging.error(f"Error during registration: {e}")  # Log the error for debugging
            flash('An error occurred during registration. Please try again.', 'danger')  # Flash error message

    return render_template('auth/register.html', form=form)  # Render the registration template

# -------------------------
# LOGOUT ROUTE
# -------------------------
@auth_bp.route('/logout')
@login_required  # Ensure the user is logged in before allowing logout
def logout():
    logout_user()  # Log the user out using Flask-Login's logout_user()
    flash('You have logged out.', 'success')  # Flash success message on logout
    return redirect(url_for('auth.login'))  # Redirect to the login page after logout
