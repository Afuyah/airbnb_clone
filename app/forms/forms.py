from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, FloatField, SelectField, TextAreaField, IntegerField, SubmitField,DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')  
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price_per_night = FloatField('Price per Night', validators=[DataRequired()])  # Updated
    bedrooms = IntegerField('Number of Bedrooms', validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create Listing')


class BookingForm(FlaskForm):
    check_in_date = DateField('Check-in Date', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('Check-out Date', format='%Y-%m-%d', validators=[DataRequired()])
    guests = IntegerField('Number of Guests', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Book Now')

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

class AmenityForm(FlaskForm):
    name = StringField('Amenity Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description', validators=[Length(max=255)])  # Optional field
    submit = SubmitField('Add Amenity')

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired()])
    latitude = DecimalField('Latitude', places=6, validators=[DataRequired()])
    longitude = DecimalField('Longitude', places=6, validators=[DataRequired()])
    submit = SubmitField('Add Location')

class SupportRequestForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=100)])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit Request')


from wtforms.validators import DataRequired, Length, Regexp

class PaymentForm(FlaskForm):
    phone_number = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Length(min=10, max=15),
            Regexp(r'^\+?\d{10,15}$', message="Please enter a valid phone number.")
        ]
    )
    submit = SubmitField('Proceed to Pay')
