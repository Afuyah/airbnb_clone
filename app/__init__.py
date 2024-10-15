from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config  # Load configuration settings

# Initialize extensions
db = SQLAlchemy()  # SQLAlchemy for ORM
migrate = Migrate()  # Migrate for database migrations
login_manager = LoginManager()  # LoginManager for user session management


# Define the function that loads a user for the session
@login_manager.user_loader
def load_user(user_id):
    from app.models.models import User
    return User.query.get(int(user_id))

# Create and configure the Flask application
def create_app():
    app = Flask(__name__)

    # Load configuration from config.py (or environment)
    app.config.from_object(Config)

    # Initialize extensions with the application
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Set the default login view for unauthorized access
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.routes.auth import auth_bp  # Authentication routes
    from app.routes.main import main_bp  # Main routes (e.g., homepage)
    from app.routes.listings import listings_bp  # Listings routes for the marketplace
    from app.routes.bookings import bookings_bp  # Booking routes
    from app.routes.reviews import reviews_bp  # Reviews routes
    from app.routes.support import support_bp  # Support request routes
    from app.routes.admin import admin_bp  # Admin dashboard routes
    from app.routes.owners import owners_bp  # Owner routes
    from app.routes.locations import locations_bp  # Location routes


    app.register_blueprint(auth_bp, url_prefix='/auth')  # Register auth blueprint
    app.register_blueprint(main_bp)  # Register main blueprint (root)
    app.register_blueprint(listings_bp, url_prefix='/listings')  # Listings prefix
    app.register_blueprint(bookings_bp, url_prefix='/bookings')  # Bookings prefix
    app.register_blueprint(reviews_bp, url_prefix='/reviews')  # Reviews prefix
    app.register_blueprint(support_bp, url_prefix='/support')  # Support prefix
    app.register_blueprint(admin_bp, url_prefix='/admin')  # Admin prefix
    app.register_blueprint(owners_bp, url_prefix='/owners')  # Owner prefix
    app.register_blueprint(locations_bp, url_prefix='/locations')  # Location prefix




    return app  # Return the Flask application instance
