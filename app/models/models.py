from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between listings and amenities
listing_amenities = db.Table(
    'listing_amenities',
    db.Column('listing_id', db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id', ondelete='CASCADE'), primary_key=True)
)

# User model with corrected relationships and password management
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=True, default='guest')

    # Relationships
    listings = db.relationship('Listing', backref='owner', lazy='dynamic', foreign_keys='Listing.owner_id', cascade='all, delete-orphan')
    listings_as_agent = db.relationship('Listing', backref='agent', lazy='dynamic', foreign_keys='Listing.agent_id', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    support_requests = db.relationship('SupportRequest', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    # Resolving relationship conflict with `overlaps` to avoid warning
    audit_logs = db.relationship('AuditLog', backref='user_audit_logs', lazy='dynamic', cascade='all, delete-orphan', overlaps="audit_logs_user,user_audit_logs")

    # Password Methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login methods
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username} (ID: {self.id}), Role: {self.role}, Email: {self.email}>'

# AuditLog model with backref and relationships resolved
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Use unique backref `audit_logs_user` in User model
    user = db.relationship('User', backref='audit_logs_user', lazy=True)

    def __repr__(self):
        return f'<AuditLog Action: {self.action}, User ID: {self.user_id}, Timestamp: {self.timestamp}>'

# Listing model with owner and agent relationships
class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), index=True, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id', ondelete='CASCADE'), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    bookings = db.relationship('Booking', backref='listing', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('Image', backref='listing', lazy='select', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='listing', lazy='dynamic', cascade='all, delete-orphan')
    amenities = db.relationship('Amenity', secondary=listing_amenities, backref=db.backref('listings', lazy='dynamic'))
    
    # Add relationship to Location
    location = db.relationship('Location', backref='listings', lazy='joined')

    def __repr__(self):
        return f'<Listing {self.title}, Price {self.price_per_night}>'


# Booking model with validation and price calculation
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=True)  # Automatically calculated
    status = db.Column(db.String(50), default='Pending')  # 'Pending', 'Confirmed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('check_out_date')
    def validate_dates(self, key, check_out_date):
        if self.check_in_date and check_out_date <= self.check_in_date:
            raise ValueError("Check-out date must be after check-in date.")
        return check_out_date

    def calculate_total_price(self):
        listing = Listing.query.get(self.listing_id)
        duration = (self.check_out_date - self.check_in_date).days
        self.total_price = duration * listing.price_per_night
        return self.total_price

    def __repr__(self):
        return f'<Booking {self.id} for Listing {self.listing_id} by User {self.user_id}>'

# Review model with rating validation
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating

    def __repr__(self):
        return f'<Review {self.id} for Listing {self.listing_id} by User {self.user_id}>'

# Amenity model
class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)

    def __repr__(self):
        return f'<Amenity {self.name}>'

# SupportRequest model with status update method
class SupportRequest(db.Model):
    __tablename__ = 'support_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Open')  # 'Open', 'In Progress', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def update_status(self, new_status):
        valid_statuses = ['Open', 'In Progress', 'Closed']
        if new_status not in valid_statuses:
            raise ValueError("Invalid status provided.")
        self.status = new_status

    def __repr__(self):
        return f'<Support Request {self.subject} by User {self.user_id}>'

# Image model
class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<Image {self.id}, URL {self.url}>'

# Location model with coordinate validation
class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)  # City or neighborhood
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    @validates('latitude')
    def validate_latitude(self, key, latitude):
        if latitude < -90 or latitude > 90:
            raise ValueError("Latitude must be between -90 and 90")
        return latitude

    @validates('longitude')
    def validate_longitude(self, key, longitude):
        if longitude < -180 or longitude > 180:
            raise ValueError("Longitude must be between -180 and 180")
        return longitude

    def __repr__(self):
        return f'<Location {self.name}, Coordinates ({self.latitude}, {self.longitude})>'