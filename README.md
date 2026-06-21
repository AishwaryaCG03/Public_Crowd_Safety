# CrowdSafe

CrowdSafe is a Flask-based crowd safety and event operations platform for organizers who need to manage attendees, monitor venue pressure, and analyze crowd risk in real time. The project combines event management, QR-based check-in, zone capacity tracking, evacuation support, and AI-assisted monitoring from both structured event data and CCTV/video feeds.

## Overview

CrowdSafe helps organizers answer questions like:

- How many people are currently inside the event?
- Which zones are approaching or exceeding capacity?
- Is the crowd state normal, busy, crowded, or critical?
- What operational risks are most likely right now?
- What immediate actions should staff take?
- What does the CCTV/video feed show about density hotspots?

The system is designed around server-rendered Flask pages plus live Socket.IO updates so monitoring screens refresh immediately when check-ins, check-outs, or video-analysis events occur.

## Current Feature Set

### Core Platform

- User registration and login for organizers
- Event creation with venue metadata and map coordinates
- Event dashboard listing all events owned by the logged-in organizer
- Event detail page with venue information and management shortcuts

### Check-In and Capacity Management

- Zone creation with max-capacity limits
- Attendee registration and QR code generation
- Manual check-in and check-out using QR values
- Real-time zone capacity updates through Socket.IO
- Current occupancy percentage per zone
- Contact tracing lookup for attendees present in a zone during a time window

### Live Monitoring

- Dedicated monitoring page per event
- Real-time crowd state classification:
  - `Normal`
  - `Busy`
  - `Crowded`
  - `Critical`
- Live risk scoring and trend visualization
- Likely cause generation based on current event conditions
- Recommended actions for operators
- Zone-by-zone crowd status table
- Occupancy and risk trend chart

### CCTV / Video AI Monitoring

- Uploaded video analysis mode
- Live CCTV camera mode using OpenCV-supported camera URLs
- Reconnect handling for live camera feeds
- Stop control for live monitoring sessions
- Person detection on video frames using OpenCV HOG detector
- Heatmap generation from observed crowd positions
- Hotspot extraction from cumulative detections
- Annotated preview frame display
- Persistent analysis results even after uploaded analysis completes or a live feed stops

### Evacuation Support

- Venue map and evacuation route view
- Zone-aware venue context for operational planning

## What Is Actually Implemented

The repository currently contains the following production-facing flows:

- Authentication
- Event CRUD
- QR attendee registration
- Zone capacity management
- Contact tracing
- Real-time monitoring page
- AI-assisted crowd risk inference
- CCTV / uploaded video analysis with heatmap output
- Evacuation route visualization

## Architecture

### Backend

- `Flask` is the main web framework
- `Flask-SQLAlchemy` handles persistence
- `Flask-Login` manages sessions and route protection
- `Flask-WTF` handles form validation
- `Flask-Bcrypt` hashes passwords
- `Flask-SocketIO` pushes live updates to the browser

### Frontend

- Server-rendered Jinja templates
- `Bootstrap 5` for layout and UI
- Vanilla JavaScript for page behavior
- `Chart.js` for trend charts
- `Leaflet.js` for map visualization
- `Socket.IO` client for live monitoring and capacity updates

### Storage

- SQLite database via `site.db`
- Uploaded media stored under `static/uploads`

### Realtime Flow

The app emits live events whenever:

- a zone is created
- an attendee checks in
- an attendee checks out
- a video-analysis job publishes a new state

These updates are broadcast to the event room through Socket.IO and reflected immediately on the monitoring page.

## AI Models and Analytics

CrowdSafe currently uses two AI / analytics layers.

### 1. Hybrid Crowd Risk Inference

File: `monitoring.py`

This is a rule-guided, tabular real-time scoring model that combines operational signals into a single monitoring payload.

#### Features and Inputs

- Zone occupancy percentage
- Near-capacity zone count
- Critical zone count
- Crowd concentration index
- Recent attendee inflow (last 15 minutes)
- Event timing pressure
- CCTV person detections
- CCTV heatmap hotspots

#### Scoring and Outputs

- **Crowd State**: `Normal`, `Busy`, `Crowded`, or `Critical`
- **Risk Level**: `Low`, `Moderate`, `High`, or `Critical`
- **Risk Score**: Numeric score from 0 to 100
- **Likely Causes**: Up to 4 identified risk factors
- **Recommendations**: Up to 4 actionable steps for operators
- **Short Summary**: Human-readable monitoring summary

#### Risk Score Calculation

The risk score is a weighted combination of:

| Factor | Weight |
|--------|--------|
| Overall Occupancy Score | 45 |
| Zone Pressure Score | 25 |
| Crowd Concentration Score | 15 |
| Recent Inflow Score | 10 |
| Video Density Score | 12 |
| Video Hotspot Score | 8 |
| Event Timing Pressure | 5 |

#### Why This Model Fits

The project already has structured operational data such as zones, capacities, attendee presence, check-in velocity, and event timing, so a real-time hybrid inference layer is the most practical model for the current application state.

### 2. CCTV / Video Person Detection Pipeline

File: `video_ai.py`

This is the computer vision layer used for live camera and uploaded video analysis.

#### Current Vision Model

- **OpenCV HOG (Histogram of Oriented Gradients) Descriptor**: Lightweight person detector suitable for real-time analysis without heavy ML libraries
- Default SVM detector from OpenCV library

#### What It Does

1. Opens uploaded video files or live CCTV camera streams
2. Samples frames at configurable intervals
3. Detects people using HOG+SVM
4. Marks estimated crowd positions
5. Builds a cumulative density grid
6. Converts density grid to normalized heatmap points
7. Extracts the strongest hotspots
8. Emits annotated preview images and summary statistics

#### Supported Modes

- `upload`: Process finite video files and retain final results
- `live`: Connect to real CCTV camera/stream URLs and continue processing until stopped

#### Video Analysis Pipeline

1. **Frame Sampling**: Samples 1 frame every N frames based on video FPS
2. **Person Detection**: Uses HOG detector to find bounding boxes
3. **Heatmap Construction**: Maps detected person centers to a grid
4. **Hotspot Extraction**: Identifies top 5 density hotspots
5. **Frame Annotation**: Draws bounding boxes and density markers on preview
6. **Live Updates**: Emits events every 3 analyzed frames

#### Video Analysis State Tracking

The system maintains detailed state for each analysis session:

- Status: idle → queued → processing → completed/stopped/error
- Frame analysis metrics: analyzed_frames, average/peak/latest people count
- Heatmap points with intensity values
- Top hotspots (normalized coordinates)
- Preview frame (base64 encoded JPEG)
- Reconnect attempts for live streams

#### Current Limitations

- HOG is lighter than YOLO-based detectors, so accuracy is not state-of-the-art
- Dense occlusions, poor lighting, and aggressive camera motion can reduce quality
- Stream success depends on whether OpenCV can open the CCTV URL from the host machine
- Video state stored in memory resets when server restarts

#### Recommended Future AI Upgrade

If you want stronger real-world crowd analytics, the next step is:

- `YOLOv8` or similar modern detector for person detection
- `ByteTrack` or `DeepSORT` for multi-person tracking
- Camera calibration for better density estimation
- Multi-camera fusion across one event

## Database Model

The main SQLAlchemy models are:

### `User`

- id (primary key)
- username (unique, 2-20 chars)
- email (unique, valid email)
- password (bcrypt-hashed, 60 chars)
- events (relationship to Event)
- date_joined (datetime)

### `Event`

- id (primary key)
- name (2-100 chars)
- objective (2-200 chars)
- target_audience (2-100 chars)
- date_time (datetime)
- venue_name (2-100 chars)
- venue_address (2-200 chars)
- latitude (float, -90 to 90)
- longitude (float, -180 to 180)
- ticket_price (float, optional)
- sponsors (200 chars, optional)
- description (text)
- date_created (datetime)
- user_id (foreign key to User)
- zones (relationship to Zone)
- attendees (relationship to Attendee)
- check_ins (relationship to CheckIn)

### `Zone`

- id (primary key)
- name (2-100 chars)
- description (text, optional)
- max_capacity (integer ≥1)
- current_capacity (integer, default 0)
- coordinates (JSON string, optional)
- event_id (foreign key to Event)
- check_ins (relationship to CheckIn)

Properties:
- `capacity_percentage`: (current_capacity / max_capacity) * 100
- `is_near_capacity`: capacity_percentage ≥ 80
- `is_over_capacity`: capacity_percentage ≥ 100

### `Attendee`

- id (primary key)
- name (2-100 chars)
- email (optional, valid)
- phone (optional, 5-20 chars)
- qr_code (unique string)
- registration_time (datetime)
- event_id (foreign key to Event)
- check_ins (relationship to CheckIn)

Properties:
- `current_zone`: Zone where attendee is currently checked in
- `is_checked_in`: Boolean

### `CheckIn`

- id (primary key)
- attendee_id (foreign key to Attendee)
- zone_id (foreign key to Zone)
- check_in_time (datetime, default now)
- check_out_time (datetime, optional)
- event_id (foreign key to Event)

Property:
- `duration`: Time delta from check-in to now or check-out time

## Main Routes

The application currently exposes these key routes:

### Public Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page |
| `/home` | GET | Home page (alias) |
| `/about` | GET | About page |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |

### Authenticated Organizer Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/dashboard` | GET | List all user events |
| `/event/new` | GET/POST | Create a new event |
| `/event/<event_id>` | GET | View event details |
| `/event/<event_id>/update` | GET/POST | Update event information |
| `/event/<event_id>/delete` | POST | Delete an event |
| `/event/<event_id>/checkin` | GET/POST | Check-in dashboard: manage zones, attendees, and check-ins |
| `/event/<event_id>/evacuation` | GET | Evacuation route map |
| `/event/<event_id>/monitoring` | GET | Live monitoring dashboard |

### Operational APIs

| Route | Method | Description |
|-------|--------|-------------|
| `/event/<event_id>/zones/new` | POST | Create a new zone for an event |
| `/event/<event_id>/scan` | POST | Check-in an attendee using QR code (JSON API) |
| `/event/<event_id>/checkout` | POST | Check-out an attendee using QR code (JSON API) |
| `/api/event/<event_id>/capacity` | GET | Get real-time zone capacities (JSON) |
| `/api/event/<event_id>/monitoring` | GET | Get current monitoring payload (JSON) |
| `/api/event/<event_id>/video_analysis` | GET | Get current video analysis state (JSON) |
| `/event/<event_id>/monitoring/video` | POST | Start video analysis (upload or CCTV) |
| `/event/<event_id>/monitoring/video/stop` | POST | Stop video analysis |
| `/api/event/<event_id>/contact_trace` | GET | Get contact tracing information for a zone |

### Socket.IO Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `join_event` | Client → Server | Subscribe to event-specific live updates |
| `monitoring_update` | Server → Client | New monitoring payload available |
| `capacity_update` | Server → Client | Zone capacity has changed |
| `video_analysis_update` | Server → Client | Video analysis has new results |

## Project Structure

```text
Public_Crowd_Safety/
├── app.py                      # Flask app bootstrap and Socket.IO init
├── routes.py                   # Main web routes and API endpoints
├── models.py                   # SQLAlchemy database models
├── forms.py                    # Flask-WTF forms definition
├── monitoring.py               # Hybrid Crowd Risk Inference logic
├── video_ai.py                 # CCTV/video analysis pipeline
├── mcp_server.py               # Optional experimental MCP server (not used by default)
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── templates/                  # Jinja HTML templates
│   ├── layout.html             # Base template with Bootstrap
│   ├── home.html               # Landing page
│   ├── about.html              # About CrowdSafe
│   ├── register.html           # User registration form
│   ├── login.html              # User login form
│   ├── dashboard.html          # Event organizer dashboard
│   ├── create_event.html       # Event creation/update form
│   ├── event.html              # Event detail view
│   ├── checkin_dashboard.html  # Check-in & capacity management
│   ├── monitoring.html         # Live monitoring dashboard
│   ├── evacuation_routes.html  # Evacuation route view
│   └── errors/                 # Error page templates
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
├── static/                     # Static assets
│   ├── css/
│   │   └── main.css            # Custom styles
│   ├── js/
│   │   └── main.js             # Frontend scripts
│   └── uploads/                # Uploaded media directory
├── instance/                   # Flask instance folder
│   └── site.db                 # SQLite database (may appear here)
└── site.db                     # SQLite database (may appear here)
```

## Technologies Used

### Backend Technologies

| Library | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.3 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM for database interactions |
| Flask-Login | 0.6.2 | User session management |
| Flask-WTF | 1.2.1 | Form handling and validation |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| Flask-SocketIO | 5.3.6 | Real-time bidirectional communication |
| python-socketio | 5.10.0 | Socket.IO library |
| python-dotenv | 1.0.0 | Environment variable loading |
| email-validator | 2.1.0 | Email validation for forms |
| gunicorn | 21.2.0 | Production WSGI server |

### Data and Storage

| Technology | Purpose |
|------------|---------|
| SQLite | Relational database |
| SQLAlchemy | ORM layer |

### Frontend Technologies

| Technology | Purpose |
|------------|---------|
| HTML5 | Markup language |
| CSS3 | Styling |
| Bootstrap 5 | Responsive UI framework |
| JavaScript | Interactive behavior |
| Jinja2 | Templating engine |
| Socket.IO client | Real-time communication |
| Chart.js | Trend chart visualization |
| Leaflet.js | Map visualization |

### AI / Computer Vision / Imaging

| Library | Version | Purpose |
|---------|---------|---------|
| opencv-python-headless | 4.10.0.84 | Computer vision and video processing |
| numpy | 1.26.4 | Numerical computations and matrix operations |
| Pillow | 10.1.0 | Image processing |
| qrcode | 7.4.2 | QR code generation |

### Mapping / Geospatial

| Library | Version | Purpose |
|---------|---------|---------|
| geopy | 2.4.1 | Geocoding and distance calculations |
| folium | 0.15.0 | Interactive map generation |

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Public_Crowd_Safety
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional Environment Variables

The app currently loads `.env` if present. The code defaults to SQLite and a hardcoded secret key, but you should override those for real use.

Example `.env`:

```env
SECRET_KEY=change_this_secret_key
DATABASE_URI=sqlite:///site.db
```

Note:

- `app.py` currently sets defaults directly in code
- If you want full `.env`-driven configuration, you can extend `app.config` accordingly

### 5. Database Setup

There is no Flask-Migrate workflow in the current implementation. The database is created automatically with `db.create_all()` when the app starts.

If `site.db` does not exist, simply run:

```bash
python app.py
```

### 6. Run the Application

```bash
python app.py
```

The app starts with Socket.IO enabled so real-time monitoring features work.

## How to Use

### Basic Event Flow

1. Register an organizer account
2. Log in
3. Create an event
4. Open the event dashboard
5. Add zones with capacities
6. Register attendees and generate QR codes
7. Use manual check-in / check-out to simulate venue occupancy
8. Open the monitoring page to observe live crowd status

### Monitoring Flow

On the monitoring page you can:

- See the current crowd state
- Track risk score and trend
- Inspect zone-by-zone status
- View likely causes and recommended actions
- Upload a CCTV/video file for analysis
- Connect a live CCTV stream URL
- Stop live video monitoring when needed
- Inspect the heatmap, hotspots, preview frame, and persisted results

### Supported CCTV / Stream Inputs

Typical examples:

- `rtsp://user:password@camera-ip:554/Streaming/Channels/101`
- `http://camera-ip/mjpeg`
- Another OpenCV-supported HTTP / RTSP stream URL

## Forms Available

The project currently uses the following forms:

- `RegistrationForm`: User registration with username, email, password
- `LoginForm`: User login with email, password, remember-me option
- `EventForm`: Event creation/update with all event metadata
- `ZoneForm`: Zone creation with name, description, max capacity
- `AttendeeForm`: Attendee registration with name, email, phone
- `CheckInForm`: Manual check-in with QR code and zone ID

These cover the main operator flow from account creation to event and attendee operations.

## Notes About Accuracy and Production Use

### Important

This project is a strong functional prototype / student-project style operational platform, but it should still be treated carefully before any real production deployment.

### Current Constraints

- SQLite is fine for development but not ideal for high-concurrency production use
- Uploaded files are stored locally
- Video-analysis state is stored in memory, so it resets when the server restarts
- The current vision model is practical but not enterprise-grade
- No formal automated test suite is included in the repository right now

### Recommended Production Improvements

- Move to PostgreSQL for better concurrency and reliability
- Move uploads to object storage (S3, Cloud Storage, etc.)
- Persist monitoring snapshots and video states in the database
- Add proper background workers for long-running analysis tasks
- Upgrade the detector to YOLO-based inference for better accuracy
- Add multi-camera management per event
- Add alerting integrations such as SMS, email, and push notifications
- Implement user roles and permissions for larger teams
- Add comprehensive logging and auditing
- Implement rate limiting and security measures
- Add automated tests

## Troubleshooting

### `python app.py` shows a restart message on Windows

Flask debug mode uses a reloader. Seeing:

```text
* Restarting with watchdog (windowsapi)
```

is normal.

### CCTV stream does not open

Check:

- The stream URL is reachable from the machine running Flask
- The username/password in the URL are correct
- The CCTV camera exposes an OpenCV-compatible stream
- Firewall rules are not blocking the connection

### Uploaded video shows no people

Possible reasons:

- Camera angle is too low or too crowded for HOG detection
- Lighting is poor
- Resolution is low
- People are partially occluded

### Monitoring results disappear after refresh

Live runtime state is kept in process memory. If the Flask process restarts, transient video-analysis state is reset.

## Additional File Notes

- `mcp_server.py` exists as a separate experimental service script and is not required for the main Flask app to run
- `static/uploads/` may contain generated or uploaded event assets
- `instance/site.db` and `site.db` may both appear depending on how the application is run

## License

This repository does not currently include a dedicated license file in the visible project structure. If you plan to share or deploy it, add an explicit license file such as `MIT`, `Apache-2.0`, or another license of your choice.
