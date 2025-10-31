from flask_login import UserMixin
from datetime import datetime
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    events = db.relationship('Event', backref='organizer', lazy=True)
    incidents = db.relationship('Incident', backref='reporter', lazy=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    objective = db.Column(db.String(200), nullable=False)
    target_audience = db.Column(db.String(100), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    venue_name = db.Column(db.String(100), nullable=False)
    venue_address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    ticket_price = db.Column(db.Float, nullable=True)
    sponsors = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    incidents = db.relationship('Incident', backref='event', lazy=True)
    restricted_areas = db.relationship('RestrictedArea', backref='event', lazy=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='event', lazy=True)
    zones = db.relationship('Zone', backref='event', lazy=True)
    attendees = db.relationship('Attendee', backref='event', lazy=True)
    check_ins = db.relationship('CheckIn', backref='event', lazy=True)
    capacity_alerts = db.relationship('CapacityAlert', backref='event', lazy=True)
    
    def __repr__(self):
        return f"Event('{self.name}', '{self.venue_name}', '{self.date_time}')"

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_type = db.Column(db.String(50), nullable=False)  # Medical, Security, Other
    description = db.Column(db.Text, nullable=False)
    location_description = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # Low, Medium, High, Critical
    status = db.Column(db.String(20), default='Reported')  # Reported, In Progress, Resolved
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f"Incident('{self.incident_type}', '{self.severity}', '{self.status}')"

class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=False)
    last_seen_location = db.Column(db.String(200), nullable=False)
    last_seen_time = db.Column(db.DateTime, nullable=False)
    reporter_name = db.Column(db.String(100), nullable=False)
    reporter_contact = db.Column(db.String(20), nullable=False)
    image_file = db.Column(db.String(20), nullable=True, default='default.jpg')
    status = db.Column(db.String(20), default='Missing')  # Missing, Found
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f"MissingPerson('{self.name}', '{self.status}')"

class MissingPersonMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # image or video
    file_path = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"MissingPersonMedia('{self.media_type}', '{self.file_path}')"

class DetectionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('missing_person_media.id'), nullable=True)
    result_type = db.Column(db.String(20), nullable=False)  # face, clothing, reid
    confidence = db.Column(db.Float, nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"DetectionResult('{self.result_type}', confidence='{self.confidence}')"

class RestrictedArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    coordinates = db.Column(db.Text, nullable=False)  # JSON string of polygon coordinates
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f"RestrictedArea('{self.name}', Event ID: '{self.event_id}')"

class BottleneckAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_description = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    density_level = db.Column(db.Float, nullable=False)  # People per square meter
    risk_level = db.Column(db.String(20), nullable=False)  # Low, Medium, High, Critical
    prediction = db.Column(db.Text, nullable=True)  # AI prediction text
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def __repr__(self):
        return f"BottleneckAlert('{self.location_description}', '{self.risk_level}')"

class CrowdDensity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    density_value = db.Column(db.Float, nullable=False)  # Normalized density 0.0-1.0
    people_count = db.Column(db.Integer, nullable=False)  # Estimated people in area
    area_radius = db.Column(db.Float, default=10.0)  # Radius in meters
    zone_name = db.Column(db.String(100), nullable=True)  # Optional zone identifier
    risk_level = db.Column(db.String(20), nullable=False)  # Low, Medium, High, Critical
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'density_value': self.density_value,
            'people_count': self.people_count,
            'area_radius': self.area_radius,
            'zone_name': self.zone_name,
            'risk_level': self.risk_level,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f"CrowdDensity('{self.zone_name}', density={self.density_value}, risk='{self.risk_level}')"

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    preferred_channels = db.Column(db.String(50), default='inapp,email')  # comma-separated: sms,email,inapp
    is_active = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def channels(self):
        return [c.strip() for c in (self.preferred_channels or '').split(',') if c.strip()]

    def __repr__(self):
        return f"EmergencyContact('{self.name}', channels='{self.preferred_channels}')"

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    max_capacity = db.Column(db.Integer, nullable=False)
    current_capacity = db.Column(db.Integer, default=0)
    coordinates = db.Column(db.Text, nullable=True)  # JSON string of polygon coordinates
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    check_ins = db.relationship('CheckIn', backref='zone', lazy=True)
    
    @property
    def capacity_percentage(self):
        if self.max_capacity == 0:
            return 0
        return (self.current_capacity / self.max_capacity) * 100
    
    @property
    def is_near_capacity(self):
        return self.capacity_percentage >= 80
    
    @property
    def is_over_capacity(self):
        return self.capacity_percentage >= 100
    
    def __repr__(self):
        return f"Zone('{self.name}', {self.current_capacity}/{self.max_capacity})"

class Attendee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    check_ins = db.relationship('CheckIn', backref='attendee', lazy=True)
    
    @property
    def current_zone(self):
        latest_checkin = CheckIn.query.filter_by(attendee_id=self.id, check_out_time=None).first()
        return latest_checkin.zone if latest_checkin else None
    
    @property
    def is_checked_in(self):
        return CheckIn.query.filter_by(attendee_id=self.id, check_out_time=None).first() is not None
    
    def __repr__(self):
        return f"Attendee('{self.name}', QR: {self.qr_code})"

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attendee_id = db.Column(db.Integer, db.ForeignKey('attendee.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    @property
    def duration(self):
        if self.check_out_time:
            return self.check_out_time - self.check_in_time
        return datetime.utcnow() - self.check_in_time
    
    def __repr__(self):
        return f"CheckIn(Attendee: {self.attendee_id}, Zone: {self.zone_id}, Time: {self.check_in_time})"

class CapacityAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # warning, critical, over_capacity
    capacity_percentage = db.Column(db.Float, nullable=False)
    current_count = db.Column(db.Integer, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"CapacityAlert(Zone: {self.zone_id}, Type: {self.alert_type}, {self.current_count}/{self.max_capacity})"
