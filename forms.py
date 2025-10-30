from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, IntegerField, DateTimeField, DateTimeLocalField
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

class IncidentForm(FlaskForm):
    incident_type = SelectField('Incident Type', choices=[('Medical', 'Medical Emergency'), ('Security', 'Security Issue'), ('Other', 'Other')], validators=[DataRequired()])
    description = TextAreaField('Incident Description', validators=[DataRequired()])
    location_description = StringField('Location Description', validators=[DataRequired(), Length(min=2, max=200)])
    latitude = FloatField('Latitude', validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[DataRequired(), NumberRange(min=-180, max=180)])
    severity = SelectField('Severity', choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')], validators=[DataRequired()])
    submit = SubmitField('Report Incident')

class MissingPersonForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Age', validators=[Optional()])
    description = TextAreaField('Description (clothing, appearance, etc.)', validators=[DataRequired()])
    last_seen_location = StringField('Last Seen Location', validators=[DataRequired(), Length(min=2, max=200)])
    last_seen_time = DateTimeLocalField('Last Seen Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    reporter_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=100)])
    reporter_contact = StringField('Your Contact Number', validators=[DataRequired(), Length(min=5, max=20)])
    image = FileField('Upload Image (if available)', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Report Missing Person')

class MissingMediaForm(FlaskForm):
    media = FileField('Upload Media (image/video)', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov'])])
    submit = SubmitField('Upload')

class RestrictedAreaForm(FlaskForm):
    name = StringField('Area Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    coordinates = TextAreaField('Coordinates (JSON format)', validators=[DataRequired()])
    submit = SubmitField('Create Restricted Area')

class EmergencyContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    role = StringField('Role', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(min=5, max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    preferred_channels = SelectField('Preferred Channels', choices=[('inapp', 'In-App'), ('email', 'Email'), ('sms', 'SMS')], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Contact')