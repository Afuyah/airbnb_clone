from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

# Association Table for Listings and Amenities
listing_amenities = db.Table('listing_amenities',
    db.Column('listing_id', db.Integer, db.ForeignKey('listings.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=True)

    # Specify foreign_keys for the owner-user relationship
    listings = db.relationship('Listing', backref='owner', lazy=True, foreign_keys='Listing.owner_id')

    # Specify foreign_keys for the agent-user relationship
    listings_as_agent = db.relationship('Listing', backref='agent', lazy=True, foreign_keys='Listing.agent_id')

    bookings = db.relationship('Booking', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    support_requests = db.relationship('SupportRequest', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

# Updated Listing Model
class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bookings = db.relationship('Booking', backref='listing', lazy=True)
    images = db.relationship('Image', backref='listing', lazy=True)
    reviews = db.relationship('Review', backref='listing', lazy=True)

    def __repr__(self):
        return f'<Listing {self.title}, Price {self.price_per_night}>'

# Booking Model
class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending')  # 'Pending', 'Confirmed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('check_out_date')
    def validate_dates(self, key, check_out_date):
        if check_out_date <= self.check_in_date:
            raise ValueError("Check-out date must be after check-in date.")
        return check_out_date

    def __repr__(self):
        return f'<Booking by User {self.user_id} for Listing {self.listing_id}>'


# Review Model
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @validates('rating')
    def validate_rating(self, key, rating):
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating

    def __repr__(self):
        return f'<Review (ID: {self.id}) for Listing {self.listing_id} by User {self.user_id}>'


class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    listings = db.relationship('Listing', secondary=listing_amenities, backref='amenities', lazy='joined')

    def __repr__(self):
        return f'<Amenity {self.name}>'


# Image Model
class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)

    def __repr__(self):
        return f'<Image {self.id}, URL {self.url}>'

# Support Request Model
class SupportRequest(db.Model):
    __tablename__ = 'support_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Open')  # 'Open', 'In Progress', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Support Request {self.subject} by User {self.user_id}>'

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # City or neighborhood
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    listings = db.relationship('Listing', backref='location', lazy=True)

    @validates('latitude', 'longitude')
    def validate_coordinates(self, key, value):
        if (key == 'latitude' and (value < -90 or value > 90)) or (key == 'longitude' and (value < -180 or value > 180)):
            raise ValueError(f"{key} must be valid")
        return value

    def __repr__(self):
        return f'<Location {self.name}>'
