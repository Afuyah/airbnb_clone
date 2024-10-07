from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import User
from app.forms.forms import RegistrationForm, LoginForm
from app import db

auth_bp = Blueprint('auth', __name__)

# Home route (optional)
@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # Redirect to login or your main page

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user instance with hashed password
        new_user = User(
            username=form.username.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)  # Use the set_password method to hash the password
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()  # Rollback the session if there's an error
            flash('An error occurred while registering. Please try again.', 'danger')
            print(f"Error: {e}")  # Log the error for debugging

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data): 
            login_user(user)
            flash('Logged in successfully!', 'success')
            # Redirect based on user role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'owner':
                return redirect(url_for('owners.dashboard'))  
            elif user.role == 'agent':
                return redirect(url_for('agents.dashboard')) 
            else:
                return redirect(url_for('main.index'))  # Default redirect for regular users
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))
