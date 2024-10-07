from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Redirect to login page for unauthorized users

from app.models.models import User 

@login_manager.user_loader
def load_user(user_id):
    """Load user from user ID."""
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)  # Load configuration from config.py

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from .routes.main import main_bp
    from .routes.owners import owners_bp
    from .routes.agents import agents_bp
    from .routes.auth import auth_bp
    from .routes.listings import listings_bp
    from .routes.bookings import bookings_bp
    from .routes.reviews import reviews_bp
    from .routes.admin import admin_bp
    from .routes.support import support_bp
    from .routes.locations import locations_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(owners_bp, url_prefix='/owners')
    app.register_blueprint(agents_bp, url_prefix='/agents')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(listings_bp, url_prefix='/listings')
    app.register_blueprint(bookings_bp, url_prefix='/bookings')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(support_bp, url_prefix='/support')
    app.register_blueprint(locations_bp, url_prefix='/locations')

    return app
