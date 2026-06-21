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
    zones = db.relationship('Zone', backref='event', lazy=True)
    attendees = db.relationship('Attendee', backref='event', lazy=True)
    check_ins = db.relationship('CheckIn', backref='event', lazy=True)
    
    def __repr__(self):
        return f"Event('{self.name}', '{self.venue_name}', '{self.date_time}')"


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

