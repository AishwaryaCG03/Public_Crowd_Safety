from flask import render_template, url_for, flash, redirect, request, jsonify, abort
from app import app, db, bcrypt, socketio
from flask_socketio import emit, join_room
from forms import RegistrationForm, LoginForm, EventForm, ZoneForm, AttendeeForm, CheckInForm
from models import User, Event, Zone, Attendee, CheckIn
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from sqlalchemy import or_
import base64
import io
import os
from monitoring import build_monitoring_payload
from werkzeug.utils import secure_filename
from video_ai import (
    analyze_video_source,
    get_video_analysis_state,
    is_allowed_video_filename,
    request_video_stop,
    reset_video_analysis_control,
    set_video_analysis_state,
)
try:
    import qrcode
except Exception:
    qrcode = None


def _owned_event_or_403(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    return event


def _monitoring_payload_for_event(event):
    zones = Zone.query.filter_by(event_id=event.id).order_by(Zone.name.asc()).all()
    active_attendees = CheckIn.query.filter_by(
        event_id=event.id,
        check_out_time=None
    ).count()
    recent_threshold = datetime.utcnow() - timedelta(minutes=15)
    recent_checkins = CheckIn.query.filter(
        CheckIn.event_id == event.id,
        CheckIn.check_in_time >= recent_threshold
    ).count()
    return build_monitoring_payload(
        event=event,
        zones=zones,
        active_attendees=active_attendees,
        recent_checkins=recent_checkins,
        video_analysis=get_video_analysis_state(event.id),
    )


def _emit_monitoring_update(event):
    payload = _monitoring_payload_for_event(event)
    socketio.emit('monitoring_update', payload, room=f"event_{event.id}")
    return payload


def _monitoring_upload_dir(event_id):
    directory = os.path.join(app.config['UPLOAD_FOLDER'], 'monitoring', str(event_id))
    os.makedirs(directory, exist_ok=True)
    return directory


def _save_monitoring_video(event_id, uploaded_file):
    filename = secure_filename(uploaded_file.filename or '')
    if not filename or not is_allowed_video_filename(filename):
        raise ValueError('Unsupported video format. Use mp4, mov, avi, mkv, webm, or m4v.')
    upload_dir = _monitoring_upload_dir(event_id)
    stamped_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    save_path = os.path.join(upload_dir, stamped_name)
    uploaded_file.save(save_path)
    return save_path, filename


def _broadcast_video_analysis_update(event_id, state):
    socketio.emit('video_analysis_update', state, room=f"event_{event_id}")
    with app.app_context():
        event = Event.query.get(event_id)
        if event:
            _emit_monitoring_update(event)
    socketio.sleep(0)


def _run_video_analysis_task(event_id, source, source_type, source_mode, source_label, job_id):
    analyze_video_source(
        event_id=event_id,
        source=source,
        source_type=source_type,
        source_mode=source_mode,
        source_label=source_label,
        emit_update=lambda state: _broadcast_video_analysis_update(event_id, state),
        job_id=job_id,
    )

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
        #set bcypt cost value to deafult value thta is 12
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


@app.route('/event/<int:event_id>/monitoring')
@login_required
def monitoring_dashboard(event_id):
    event = _owned_event_or_403(event_id)
    return render_template('monitoring.html', title='Live Monitoring', event=event)

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







# Evacuation Routes
@app.route('/event/<int:event_id>/evacuation')
@login_required
def evacuation_routes(event_id):
    event = Event.query.get_or_404(event_id)
    zones = Zone.query.filter_by(event_id=event.id).all()
    return render_template(
        'evacuation_routes.html',
        title='Evacuation Routes',
        event=event,
        zones=zones
    )


def _qr_png_base64(data: str) -> str:
    if not qrcode:
        return ''
    try:
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        print('QR generation error:', e)
        return ''

@app.route('/event/<int:event_id>/checkin', methods=['GET', 'POST'])
@login_required
def checkin_dashboard(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer != current_user:
        abort(403)
    zone_form = ZoneForm()
    attendee_form = AttendeeForm()
    checkin_form = CheckInForm()
    zones = Zone.query.filter_by(event_id=event.id).all()
    attendees = Attendee.query.filter_by(event_id=event.id).order_by(Attendee.registration_time.desc()).limit(20).all()
    qr_image = None
    if request.method == 'POST' and attendee_form.validate_on_submit():
        import uuid
        qr_code = str(uuid.uuid4())
        attendee = Attendee(
            name=attendee_form.name.data,
            email=attendee_form.email.data,
            phone=attendee_form.phone.data,
            qr_code=qr_code,
            event_id=event.id
        )
        db.session.add(attendee)
        db.session.commit()
        b64 = _qr_png_base64(qr_code)
        qr_image = f"data:image/png;base64,{b64}" if b64 else None
        flash('Attendee registered and QR generated.', 'success')
    return render_template('checkin_dashboard.html', title='Check-In & Capacity', event=event, zones=zones, attendees=attendees, zone_form=zone_form, attendee_form=attendee_form, checkin_form=checkin_form, qr_image=qr_image)

@app.route('/event/<int:event_id>/zones/new', methods=['POST'])
@login_required
def create_zone(event_id):
    event = _owned_event_or_403(event_id)
    form = ZoneForm()
    if form.validate_on_submit():
        zone = Zone(
            name=form.name.data,
            description=form.description.data or '',
            max_capacity=form.max_capacity.data,
            coordinates=form.coordinates.data or '',
            event_id=event.id
        )
        db.session.add(zone)
        db.session.commit()
        _emit_monitoring_update(event)
        flash('Zone created.', 'success')
    else:
        flash('Invalid zone data.', 'danger')
    return redirect(url_for('checkin_dashboard', event_id=event.id))

@app.route('/event/<int:event_id>/scan', methods=['POST'])
@login_required
def scan_checkin(event_id):
    event = _owned_event_or_403(event_id)
    data = request.get_json() or {}
    qr_code = (data.get('qr_code') or '').strip()
    zone_id = data.get('zone_id')
    if not qr_code or not zone_id:
        return jsonify({'ok': False, 'error': 'Missing qr_code or zone_id'}), 400
    attendee = Attendee.query.filter_by(event_id=event.id, qr_code=qr_code).first()
    zone = Zone.query.filter_by(event_id=event.id, id=zone_id).first()
    if not attendee or not zone:
        return jsonify({'ok': False, 'error': 'Invalid attendee or zone'}), 404
    active = CheckIn.query.filter_by(event_id=event.id, attendee_id=attendee.id, check_out_time=None).first()
    if active:
        return jsonify({'ok': False, 'error': 'Attendee already checked in'}), 400
    checkin = CheckIn(attendee_id=attendee.id, zone_id=zone.id, event_id=event.id)
    db.session.add(checkin)
    zone.current_capacity = (zone.current_capacity or 0) + 1
    db.session.commit()
    socketio.emit('capacity_update', {
        'event_id': event.id,
        'zone_id': zone.id,
        'current_capacity': zone.current_capacity,
        'max_capacity': zone.max_capacity,
        'capacity_percentage': zone.capacity_percentage
    }, room=f"event_{event.id}")
    _emit_monitoring_update(event)
    return jsonify({'ok': True, 'attendee_id': attendee.id, 'zone_id': zone.id})

@app.route('/event/<int:event_id>/checkout', methods=['POST'])
@login_required
def scan_checkout(event_id):
    event = _owned_event_or_403(event_id)
    data = request.get_json() or {}
    qr_code = (data.get('qr_code') or '').strip()
    if not qr_code:
        return jsonify({'ok': False, 'error': 'Missing qr_code'}), 400
    attendee = Attendee.query.filter_by(event_id=event.id, qr_code=qr_code).first()
    if not attendee:
        return jsonify({'ok': False, 'error': 'Invalid attendee'}), 404
    active = CheckIn.query.filter_by(event_id=event.id, attendee_id=attendee.id, check_out_time=None).first()
    if not active:
        return jsonify({'ok': False, 'error': 'Attendee not checked in'}), 400
    active.check_out_time = datetime.utcnow()
    zone = Zone.query.get(active.zone_id)
    zone.current_capacity = max(0, (zone.current_capacity or 0) - 1)
    db.session.commit()
    socketio.emit('capacity_update', {
        'event_id': event.id,
        'zone_id': zone.id,
        'current_capacity': zone.current_capacity,
        'max_capacity': zone.max_capacity,
        'capacity_percentage': zone.capacity_percentage
    }, room=f"event_{event.id}")
    _emit_monitoring_update(event)
    return jsonify({'ok': True, 'attendee_id': attendee.id, 'zone_id': zone.id})

@app.route('/api/event/<int:event_id>/capacity')
@login_required
def api_event_capacity(event_id):
    event = _owned_event_or_403(event_id)
    zones = Zone.query.filter_by(event_id=event.id).all()
    return jsonify({
        'event_id': event.id,
        'zones': [
            {
                'id': z.id,
                'name': z.name,
                'current_capacity': z.current_capacity,
                'max_capacity': z.max_capacity,
                'capacity_percentage': z.capacity_percentage
            } for z in zones
        ]
    })


@app.route('/api/event/<int:event_id>/monitoring')
@login_required
def api_event_monitoring(event_id):
    event = _owned_event_or_403(event_id)
    payload = _monitoring_payload_for_event(event)
    return jsonify(payload)


@app.route('/api/event/<int:event_id>/video_analysis')
@login_required
def api_event_video_analysis(event_id):
    event = _owned_event_or_403(event_id)
    return jsonify(get_video_analysis_state(event.id))


@app.route('/event/<int:event_id>/monitoring/video', methods=['POST'])
@login_required
def start_event_video_analysis(event_id):
    event = _owned_event_or_403(event_id)
    source_url = (request.form.get('source_url') or '').strip()
    source_mode = (request.form.get('source_mode') or '').strip().lower()
    video_file = request.files.get('video_file')

    if video_file and video_file.filename:
        try:
            source, source_label = _save_monitoring_video(event.id, video_file)
        except ValueError as exc:
            return jsonify({'ok': False, 'error': str(exc)}), 400
        source_type = 'upload'
        source_mode = 'upload'
    elif source_url:
        source = source_url
        source_label = source_url
        source_type = 'cctv'
        source_mode = 'live'
    else:
        return jsonify({'ok': False, 'error': 'Provide a CCTV/video file or a live stream URL.'}), 400

    request_video_stop(event.id)
    control = reset_video_analysis_control(event.id)
    job_id = control.get('job_id')
    initial_state = {
        'event_id': event.id,
        'job_id': job_id,
        'status': 'queued',
        'source_type': source_type,
        'source_mode': source_mode,
        'source_label': source_label,
        'progress': 0,
        'analyzed_frames': 0,
        'latest_people_count': 0,
        'average_people_count': 0,
        'peak_people_count': 0,
        'result_available': False,
        'last_result': None,
        'heatmap_points': [],
        'hotspots': [],
        'preview_frame': None,
        'started_at': datetime.utcnow().isoformat(),
        'finished_at': None,
        'reconnect_attempts': 0,
        'updated_at': datetime.utcnow().isoformat(),
        'message': 'CCTV/video AI job queued. Analysis will begin shortly.',
        'error': None,
    }
    set_video_analysis_state(event.id, initial_state)
    socketio.emit('video_analysis_update', initial_state, room=f"event_{event.id}")
    _emit_monitoring_update(event)
    socketio.start_background_task(_run_video_analysis_task, event.id, source, source_type, source_mode, source_label, job_id)

    return jsonify({
        'ok': True,
        'message': 'CCTV/video AI analysis started.',
        'source_type': source_type,
        'source_mode': source_mode,
        'source_label': source_label,
    })


@app.route('/event/<int:event_id>/monitoring/video/stop', methods=['POST'])
@login_required
def stop_event_video_analysis(event_id):
    event = _owned_event_or_403(event_id)
    current_state = get_video_analysis_state(event.id)
    request_video_stop(event.id)

    if current_state.get('status') in {'idle', 'completed', 'stopped', 'error'}:
        current_state['status'] = 'stopped'
        current_state['message'] = 'Video monitoring is not currently running. Latest analyzed results remain available.'
        current_state['finished_at'] = datetime.utcnow().isoformat()
        set_video_analysis_state(event.id, current_state)
        socketio.emit('video_analysis_update', current_state, room=f"event_{event.id}")
        _emit_monitoring_update(event)
        return jsonify({'ok': True, 'message': current_state['message']})

    return jsonify({
        'ok': True,
        'message': 'Stop request sent. Live CCTV/video analysis will end shortly.',
    })


@app.route('/api/event/<int:event_id>/contact_trace')
@login_required
def api_contact_trace(event_id):
    event = _owned_event_or_403(event_id)
    zone_id = request.args.get('zone_id', type=int)
    minutes = request.args.get('minutes', default=60, type=int)
    minutes = min(max(minutes, 5), 720)

    zone = Zone.query.filter_by(event_id=event.id, id=zone_id).first()
    if not zone:
        return jsonify({'ok': False, 'error': 'Zone not found'}), 404

    since = datetime.utcnow() - timedelta(minutes=minutes)
    checkins = CheckIn.query.filter(
        CheckIn.event_id == event.id,
        CheckIn.zone_id == zone.id,
        CheckIn.check_in_time <= datetime.utcnow(),
        or_(
            CheckIn.check_out_time == None,
            CheckIn.check_out_time >= since,
            CheckIn.check_in_time >= since,
        )
    ).order_by(CheckIn.check_in_time.desc()).all()

    attendees = []
    for checkin in checkins:
        if checkin.attendee_id is None:
            continue
        attendees.append({
            'name': checkin.attendee.name,
            'email': checkin.attendee.email or '',
            'phone': checkin.attendee.phone or '',
            'check_in_time': checkin.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if checkin.check_in_time else '',
            'check_out_time': checkin.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if checkin.check_out_time else 'Active',
        })

    return jsonify({
        'ok': True,
        'event_id': event.id,
        'zone_id': zone.id,
        'minutes': minutes,
        'attendees': attendees,
    })


@socketio.on('join_event')
def handle_join_event(data):
    event_id = (data or {}).get('event_id')
    if not event_id:
        return
    join_room(f"event_{event_id}")
    try:
        event = Event.query.get(int(event_id))
        if event:
            emit('monitoring_update', _monitoring_payload_for_event(event))
    except Exception:
        return


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
