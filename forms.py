from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, IntegerField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from flask_login import current_user
from datetime import datetime

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
            
    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(min=2, max=100)])
    objective = StringField('Event Objective/Goal', validators=[DataRequired(), Length(min=2, max=200)])
    target_audience = StringField('Target Audience', validators=[DataRequired(), Length(min=2, max=100)])
    date_time = DateTimeLocalField('Date and Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    venue_name = StringField('Venue Name', validators=[DataRequired(), Length(min=2, max=100)])
    venue_address = StringField('Venue Address', validators=[DataRequired(), Length(min=2, max=200)])
    latitude = FloatField('Latitude', validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[DataRequired(), NumberRange(min=-180, max=180)])
    ticket_price = FloatField('Ticket Price (if applicable)', validators=[Optional()])
    sponsors = StringField('Sponsors (if applicable)', validators=[Optional(), Length(max=200)])
    description = TextAreaField('Event Description', validators=[DataRequired()])
    submit = SubmitField('Create Event')

class ZoneForm(FlaskForm):
    name = StringField('Zone Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    max_capacity = IntegerField('Max Capacity', validators=[DataRequired(), NumberRange(min=1)])
    coordinates = TextAreaField('Coordinates (JSON)', validators=[Optional()])
    submit = SubmitField('Create Zone')

class AttendeeForm(FlaskForm):
    name = StringField('Attendee Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(min=5, max=20)])
    submit = SubmitField('Register & Generate QR')

class CheckInForm(FlaskForm):
    qr_code = StringField('QR Code', validators=[DataRequired(), Length(min=3, max=200)])
    zone_id = IntegerField('Zone ID', validators=[DataRequired()])
    submit = SubmitField('Check In')
