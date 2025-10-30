from flask import render_template, url_for, flash, redirect, request, jsonify, abort, Response
from flask import stream_with_context
from app import app, db, bcrypt, socketio
from flask_socketio import join_room, leave_room, emit
from forms import RegistrationForm, LoginForm, EventForm, IncidentForm, MissingPersonForm, RestrictedAreaForm, MissingMediaForm, EmergencyContactForm
from models import User, Event, Incident, MissingPerson, RestrictedArea, BottleneckAlert, MissingPersonMedia, DetectionResult, EmergencyContact
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from flask_mail import Message
from twilio.rest import Client

# Home route
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

# About route
@app.route('/about')
def about():
    return render_template('about.html', title='About')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

# User Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

# User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    events = Event.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', events=events)

# Create Event
@app.route('/event/new', methods=['GET', 'POST'])
@login_required
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            name=form.name.data,
            objective=form.objective.data,
            target_audience=form.target_audience.data,
            date_time=form.date_time.data,
            venue_name=form.venue_name.data,
            venue_address=form.venue_address.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            ticket_price=form.ticket_price.data,
            sponsors=form.sponsors.data,
            description=form.description.data,
            organizer=current_user
        )
        db.session.add(event)
        db.session.commit()
        flash('Your event has been created!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_event.html', title='New Event', form=form, legend='New Event')

# View Event
@app.route('/event/<int:event_id>')
def event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event.html', title=event.name, event=event)

# Update Event
@app.route('/event/<int:event_id>/update', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        event.name = form.name.data
        event.objective = form.objective.data
        event.target_audience = form.target_audience.data
        event.date_time = form.date_time.data
        event.venue_name = form.venue_name.data
        event.venue_address = form.venue_address.data
        event.latitude = form.latitude.data
        event.longitude = form.longitude.data
        event.ticket_price = form.ticket_price.data
        event.sponsors = form.sponsors.data
        event.description = form.description.data
        db.session.commit()
        flash('Your event has been updated!', 'success')
        return redirect(url_for('event', event_id=event.id))
    elif request.method == 'GET':
        form.name.data = event.name
        form.objective.data = event.objective
        form.target_audience.data = event.target_audience
        form.date_time.data = event.date_time
        form.venue_name.data = event.venue_name
        form.venue_address.data = event.venue_address
        form.latitude.data = event.latitude
        form.longitude.data = event.longitude
        form.ticket_price.data = event.ticket_price
        form.sponsors.data = event.sponsors
        form.description.data = event.description
    return render_template('create_event.html', title='Update Event', form=form, legend='Update Event')

# Delete Event
@app.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash('Your event has been deleted!', 'success')
    return redirect(url_for('dashboard'))

# Report Incident
@app.route('/event/<int:event_id>/incident/new', methods=['GET', 'POST'])
@login_required
def new_incident(event_id):
    event = Event.query.get_or_404(event_id)
    form = IncidentForm()
    if form.validate_on_submit():
        incident = Incident(
            incident_type=form.incident_type.data,
            description=form.description.data,
            location_description=form.location_description.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            severity=form.severity.data,
            reporter=current_user,
            event=event
        )
        db.session.add(incident)
        db.session.commit()
        # Automated alert trigger based on severity
        if incident.severity in ['High', 'Critical']:
            broadcast_incident_alert(incident)
        flash('Incident has been reported!', 'success')
        return redirect(url_for('event', event_id=event.id))
    return render_template('create_incident.html', title='Report Incident', form=form, legend='Report Incident', event=event)

# View Incidents for an Event
@app.route('/event/<int:event_id>/incidents')
@login_required
def event_incidents(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    incidents = Incident.query.filter_by(event_id=event.id).order_by(Incident.timestamp.desc()).all()
    return render_template('event_incidents.html', title='Event Incidents', incidents=incidents, event=event)

# View Incident Detail
@app.route('/incident/<int:incident_id>')
@login_required
def view_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    event = incident.event
    # Allow organizer or reporter to view
    if event.organizer != current_user and incident.reporter != current_user:
        abort(403)
    return render_template('incident_detail.html', title=f"Incident #{incident.id}", incident=incident, event=event)

# Report Missing Person
@app.route('/event/<int:event_id>/missing/new', methods=['GET', 'POST'])
@login_required
def report_missing(event_id):
    event = Event.query.get_or_404(event_id)
    form = MissingPersonForm()
    if form.validate_on_submit():
        missing_person = MissingPerson(
            name=form.name.data,
            age=form.age.data,
            description=form.description.data,
            last_seen_location=form.last_seen_location.data,
            last_seen_time=form.last_seen_time.data,
            reporter_name=form.reporter_name.data,
            reporter_contact=form.reporter_contact.data,
            event_id=event.id
        )
        db.session.add(missing_person)
        db.session.commit()

        # Save uploaded reference image if provided
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            person_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'missing', str(missing_person.id))
            os.makedirs(person_dir, exist_ok=True)
            file_path = os.path.join(person_dir, filename)
            form.image.data.save(file_path)
            # store relative path
            relative_path = os.path.join('uploads', 'missing', str(missing_person.id), filename)
            missing_person.image_file = relative_path
            db.session.commit()
        flash('Missing person report has been submitted!', 'success')
        return redirect(url_for('event', event_id=event.id))
    return render_template('report_missing.html', title='Report Missing Person', form=form, legend='Report Missing Person', event=event)

# View Missing Persons for an Event
@app.route('/event/<int:event_id>/missing')
@login_required
def event_missing(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    missing_persons = MissingPerson.query.filter_by(event_id=event.id).order_by(MissingPerson.timestamp.desc()).all()
    return render_template('event_missing.html', title='Missing Persons', missing_persons=missing_persons, event=event)

# View Missing Person Detail, manage media and run detection
@app.route('/missing/<int:person_id>', methods=['GET', 'POST'])
@login_required
def missing_detail(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    event = Event.query.get_or_404(person.event_id)
    if event.organizer != current_user:
        abort(403)
    media_form = MissingMediaForm()
    if request.method == 'POST' and media_form.validate_on_submit():
        if not media_form.media.data:
            flash('Please select a file to upload.', 'warning')
            return redirect(url_for('missing_detail', person_id=person.id))
        filename = secure_filename(media_form.media.data.filename)
        ext = filename.rsplit('.', 1)[-1].lower()
        media_type = 'video' if ext in ['mp4', 'avi', 'mov'] else 'image'
        person_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'missing', str(person.id), 'evidence')
        os.makedirs(person_dir, exist_ok=True)
        file_path = os.path.join(person_dir, filename)
        media_form.media.data.save(file_path)
        # Use forward slashes for web URLs
        relative_path = '/'.join(['uploads', 'missing', str(person.id), 'evidence', filename])
        media_rec = MissingPersonMedia(
            missing_person_id=person.id,
            event_id=event.id,
            uploaded_by_user_id=current_user.id,
            media_type=media_type,
            file_path=relative_path
        )
        db.session.add(media_rec)
        db.session.commit()
        flash('Media uploaded successfully.', 'success')
        return redirect(url_for('missing_detail', person_id=person.id))

    media_items = MissingPersonMedia.query.filter_by(missing_person_id=person.id).order_by(MissingPersonMedia.timestamp.desc()).all()
    results = DetectionResult.query.filter_by(missing_person_id=person.id).order_by(DetectionResult.timestamp.desc()).all()
    return render_template('missing_detail.html', title=f"Missing: {person.name}", person=person, event=event, media_form=media_form, media_items=media_items, results=results)

# Trigger detection on uploaded media (stub)
@app.route('/missing/<int:person_id>/detect', methods=['POST'])
@login_required
def run_detection(person_id):
    person = MissingPerson.query.get_or_404(person_id)
    event = Event.query.get_or_404(person.event_id)
    if event.organizer != current_user:
        abort(403)
    media_items = MissingPersonMedia.query.filter_by(missing_person_id=person.id).all()
    if not media_items:
        flash('No media to analyze. Please upload images or videos.', 'warning')
        return redirect(url_for('missing_detail', person_id=person.id))
    # Basic stub: record a pending detection result entry for each media
    for m in media_items:
        result = DetectionResult(
            missing_person_id=person.id,
            media_id=m.id,
            result_type='face',
            confidence=None,
            details=f"Detection pending for {m.file_path}."
        )
        db.session.add(result)
    db.session.commit()
    flash('Detection job queued (stub). Results will appear below.', 'info')
    return redirect(url_for('missing_detail', person_id=person.id))

# Create Restricted Area
@app.route('/event/<int:event_id>/restricted/new', methods=['GET', 'POST'])
@login_required
def new_restricted_area(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    form = RestrictedAreaForm()
    if form.validate_on_submit():
        restricted_area = RestrictedArea(
            name=form.name.data,
            description=form.description.data,
            coordinates=form.coordinates.data,
            event=event
        )
        db.session.add(restricted_area)
        db.session.commit()
        flash('Restricted area has been created!', 'success')
        return redirect(url_for('event', event_id=event.id))
    return render_template('create_restricted_area.html', title='New Restricted Area', form=form, legend='New Restricted Area', event=event)

# Bottleneck Analysis Dashboard
@app.route('/event/<int:event_id>/bottleneck')
@login_required
def bottleneck_analysis(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    alerts = BottleneckAlert.query.filter_by(event_id=event.id).order_by(BottleneckAlert.timestamp.desc()).all()
    return render_template('bottleneck_analysis.html', title='Bottleneck Analysis', alerts=alerts, event=event)

# API endpoint for AI chatbot
@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot():
    data = request.json
    event_id = data.get('event_id')
    query = data.get('query')
    zone = data.get('zone')
    
    # This would be replaced with actual AI processing
    response = {
        'answer': f"Analysis for zone {zone}: Currently moderate crowd density observed. Prediction for next 20 minutes: Potential bottleneck forming near the main entrance due to increased arrival rate. Recommend opening additional entry points."
    }

    return jsonify(response)

# Streaming Gemini AI responses over Server-Sent Events (SSE)
@app.route('/api/chatbot/stream', methods=['GET'])
@login_required
def chatbot_stream():
    event_id = request.args.get('event_id')
    query = request.args.get('query')
    zone = request.args.get('zone')

    def generate():
        api_key = os.environ.get('GOOGLE_API_K')
        if not api_key:
            yield f"event: error\ndata: {json.dumps({'error': 'GOOGLE_API_KEY not set'})}\n\n"
            return

        genai.configure(api_key=api_key)
        # Use a fast, cost‑efficient model for realtime UX
        model = genai.GenerativeModel("gemini-1.5-flash")

        system_prompt = (
            "You are CrowdSafe, a concise, helpful assistant for event crowd "
            "safety. When asked, provide short, actionable guidance. "
            f"Event ID: {event_id}. Zone: {zone}."
        )
        user_prompt = query or ""
        full_prompt = system_prompt + "\n\nUser question: " + user_prompt

        try:
            # Stream tokens as they arrive
            for chunk in model.generate_content(full_prompt, stream=True):
                text = getattr(chunk, 'text', '') or ''
                if text:
                    # Send each delta as an SSE message
                    yield f"data: {json.dumps({'delta': text})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
    # Recommended SSE headers to reduce buffering and caching
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Connection'] = 'keep-alive'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp

# ==========================
# Real-time Crowd Density IO
# ==========================
active_simulations = {}

def _risk_from_intensity(x):
    if x >= 0.8:
        return 'Critical'
    if x >= 0.6:
        return 'High'
    if x >= 0.4:
        return 'Medium'
    return 'Low'

def simulate_density(event_id):
    import random
    import time
    from models import Event
    # Ensure DB access happens within app context
    with app.app_context():
        event = Event.query.get(event_id)
        if not event:
            return
        # Simple simulation around venue coordinates
        while active_simulations.get(event_id):
            points = []
            for _ in range(25):
                lat = event.latitude + random.uniform(-0.001, 0.001)
                lng = event.longitude + random.uniform(-0.001, 0.001)
                intensity = max(0.0, min(1.0, random.random() * 1.2))
                risk = _risk_from_intensity(intensity)
                points.append({'lat': lat, 'lng': lng, 'intensity': intensity, 'risk': risk})

            critical_count = sum(1 for p in points if p['intensity'] >= 0.8)
            alert = None
            if critical_count >= 5:
                alert = {
                    'message': 'Predictive overflow detected near main area. Open additional exits.',
                    'level': 'Critical'
                }
                # Compute centroid of critical points and average intensity, then broadcast to contacts
                crit_points = [p for p in points if p['intensity'] >= 0.8]
                if crit_points:
                    avg_lat = sum(p['lat'] for p in crit_points) / len(crit_points)
                    avg_lng = sum(p['lng'] for p in crit_points) / len(crit_points)
                    avg_intensity = sum(p['intensity'] for p in crit_points) / len(crit_points)
                    try:
                        broadcast_bottleneck_alert(event, 'Critical', alert['message'], avg_lat, avg_lng, density_level=round(avg_intensity * 10.0, 2), prediction='Overflow likely within 10 minutes; open additional exits')
                    except Exception as e:
                        print('Broadcast bottleneck error:', e)

            socketio.emit('density_update', {
                'event_id': event_id,
                'points': points,
                'stats': {
                    'critical': critical_count,
                    'total': len(points)
                },
                'alert': alert
            }, room=f"event_{event_id}")
            time.sleep(2)

@socketio.on('join_event')
def on_join_event(data):
    try:
        event_id = int(data.get('event_id'))
    except Exception:
        return
    join_room(f"event_{event_id}")
    # Start simulation if not already running
    if not active_simulations.get(event_id):
        active_simulations[event_id] = True
        socketio.start_background_task(simulate_density, event_id)

@socketio.on('leave_event')
def on_leave_event(data):
    try:
        event_id = int(data.get('event_id'))
    except Exception:
        return
    leave_room(f"event_{event_id}")

# Evacuation Routes
@app.route('/event/<int:event_id>/evacuation')
@login_required
def evacuation_routes(event_id):
    event = Event.query.get_or_404(event_id)
    # Provide incidents and restricted areas to inform safer routing
    incidents = Incident.query.filter_by(event_id=event.id).all()
    restricted_areas = RestrictedArea.query.filter_by(event_id=event.id).all()

    # Serialize to JSON-friendly structures for the template
    incidents_data = [
        {
            'id': inc.id,
            'latitude': inc.latitude,
            'longitude': inc.longitude,
            'severity': inc.severity,
            'status': inc.status,
            'timestamp': inc.timestamp.isoformat()
        } for inc in incidents
    ]

    restricted_areas_data = [
        {
            'id': ra.id,
            'name': ra.name,
            'description': ra.description,
            'coordinates': ra.coordinates
        } for ra in restricted_areas
    ]
    return render_template(
        'evacuation_routes.html',
        title='Evacuation Routes',
        event=event,
        incidents=incidents_data,
        restricted_areas=restricted_areas_data
    )

# ==========================
# Emergency Contacts & Alerts
# ==========================

def _send_email(subject, recipients, body):
    if not app.config.get('MAIL_SERVER'):
        print('[Email disabled] Would send email:', subject, recipients, body)
        return
    try:
        msg = Message(subject=subject, recipients=recipients, body=body, sender=app.config.get('MAIL_DEFAULT_SENDER'))
        from app import mail
        mail.send(msg)
    except Exception as e:
        print('Email error:', e)

def _send_sms(recipients, body):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    if not (sid and token and from_number):
        print('[SMS disabled] Would send SMS to:', recipients, body)
        return
    try:
        client = Client(sid, token)
        for r in recipients:
            if r:
                client.messages.create(to=r, from_=from_number, body=body)
    except Exception as e:
        print('SMS error:', e)

def broadcast_incident_alert(incident: Incident):
    event = incident.event
    contacts = EmergencyContact.query.filter_by(event_id=event.id, is_active=True).all()
    # Prepare message
    subject = f"[CrowdSafe] {incident.severity} Incident: {incident.incident_type}"
    body = (
        f"Incident Type: {incident.incident_type}\n"
        f"Severity: {incident.severity}\n"
        f"Location: {incident.location_description} ({incident.latitude}, {incident.longitude})\n"
        f"Description: {incident.description}\n"
        f"Event: {event.name}"
    )
    # Collect recipients by channel
    email_recipients = [c.email for c in contacts if c and c.email and ('email' in c.channels())]
    sms_recipients = [c.phone for c in contacts if c and c.phone and ('sms' in c.channels())]
    # In-app notifications via Socket.IO
    socketio.emit('alert_broadcast', {
        'event_id': event.id,
        'type': 'incident',
        'severity': incident.severity,
        'title': subject,
        'message': body,
        'incident_id': incident.id,
        'timestamp': incident.timestamp.isoformat()
    }, room=f"event_{event.id}")
    # Email and SMS
    _send_email(subject, email_recipients, body)
    _send_sms(sms_recipients, body)

def broadcast_bottleneck_alert(event: Event, risk_level: str, message: str, latitude: float, longitude: float, density_level: float = None, prediction: str = None):
    contacts = EmergencyContact.query.filter_by(event_id=event.id, is_active=True).all()
    subject = f"[CrowdSafe] {risk_level} Bottleneck Alert"
    body = (
        f"Risk Level: {risk_level}\n"
        f"Location: ({latitude:.6f}, {longitude:.6f})\n"
        f"Details: {message}\n"
        f"Event: {event.name}"
    )
    try:
        alert = BottleneckAlert(
            location_description='Predicted Overflow Area',
            latitude=latitude,
            longitude=longitude,
            density_level=density_level or 0.0,
            risk_level=risk_level,
            prediction=prediction,
            event_id=event.id
        )
        db.session.add(alert)
        db.session.commit()
    except Exception as e:
        print('Persist bottleneck alert error:', e)

    socketio.emit('alert_broadcast', {
        'event_id': event.id,
        'type': 'bottleneck',
        'severity': risk_level,
        'title': subject,
        'message': body,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f"event_{event.id}")

    email_recipients = [c.email for c in contacts if c and c.email and ('email' in c.channels())]
    sms_recipients = [c.phone for c in contacts if c and c.phone and ('sms' in c.channels())]
    _send_email(subject, email_recipients, body)
    _send_sms(sms_recipients, body)

@app.route('/event/<int:event_id>/contacts', methods=['GET', 'POST'])
@login_required
def event_contacts(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    form = EmergencyContactForm()
    if form.validate_on_submit():
        contact = EmergencyContact(
            event_id=event.id,
            name=form.name.data,
            role=form.role.data,
            phone=form.phone.data,
            email=form.email.data,
            preferred_channels=form.preferred_channels.data,
            is_active=form.is_active.data
        )
        db.session.add(contact)
        db.session.commit()
        flash('Emergency contact added.', 'success')
        return redirect(url_for('event_contacts', event_id=event.id))
    contacts = EmergencyContact.query.filter_by(event_id=event.id).order_by(EmergencyContact.timestamp.desc()).all()
    return render_template('event_contacts.html', title='Emergency Contacts', event=event, form=form, contacts=contacts)

@app.route('/event/<int:event_id>/contacts/<int:contact_id>/toggle', methods=['POST'])
@login_required
def toggle_contact(event_id, contact_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    contact = EmergencyContact.query.get_or_404(contact_id)
    if contact.event_id != event.id:
        abort(403)
    contact.is_active = not contact.is_active
    db.session.commit()
    flash('Contact status updated.', 'info')
    return redirect(url_for('event_contacts', event_id=event.id))

# Error handlers
@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500