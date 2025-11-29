# CrowdSafe: Crowd Disaster Prevention and Management System

CrowdSafe is a comprehensive Flask-based application designed to help event organizers prevent and manage crowd-related disasters through predictive analytics, real-time monitoring, and intelligent response systems.

## Features

- **User Authentication**: Secure signup and login system for event organizers
- **Event Management**: Create and manage events with detailed information and geographical coordinates
- **Predictive Bottleneck Analysis**: AI-powered monitoring of crowd density and movement patterns
- **AI Chatbot Assistant**: Get real-time insights about crowd conditions in specific zones
- **Incident Reporting**: Log and manage emergency situations with response unit simulation
- **Intelligent Evacuation System**: Navigate individuals to safety with optimal exit routes
- **Lost Person Detection**: AI-powered analysis to locate missing individuals
- **Geofencing Alert System**: Monitor restricted areas and receive unauthorized entry notifications
- **QR Check-In & Capacity Management**: Digital attendee tracking with QR codes, real-time capacity monitoring, automated capacity warnings, and contact tracing capabilities

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   Note: The QR Check-In feature requires the `qrcode` and `pypng` packages, which are included in requirements.txt.
   
4. Set up environment variables in a `.env` file:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URI=sqlite:///site.db
   MAIL_SERVER=smtp.example.com  # For email alerts
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@example.com
   MAIL_PASSWORD=your_email_password
   TWILIO_ACCOUNT_SID=your_twilio_sid  # For SMS alerts
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_phone
   ```
5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
6. Run the application:
   ```
   python app.py
   ```

## Usage

1. Register a new account or login with existing credentials
2. Create a new event with all required details, including geographical coordinates
3. Access the event dashboard to utilize various management tools:
   - View bottleneck analysis with predictive insights
   - Report and manage incidents
   - Configure evacuation routes
   - Set up missing person detection
   - Create geofenced restricted areas
   - Use the AI chatbot for real-time zone-specific information
   - Manage attendee check-ins and zone capacities

### QR Check-In & Capacity Management

The QR Check-In & Capacity Management feature provides comprehensive crowd monitoring capabilities:

1. **Zone Management**: Create zones with maximum capacity limits
2. **Attendee Registration**: Register attendees and generate unique QR codes
3. **Digital Check-In/Check-Out**: Scan QR codes or manually enter codes for check-in/out
4. **Real-Time Capacity Monitoring**: Track current occupancy of each zone with percentage indicators
5. **Automated Capacity Alerts**: Receive warnings when zones approach (≥80%) or exceed capacity
6. **Contact Tracing**: Identify all attendees present in a specific zone during a selected time window
7. **Multi-Channel Alerts**: Capacity alerts are sent via in-app notifications, email, and SMS based on emergency contact preferences

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-SocketIO
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5, Socket.IO
- **Maps**: Leaflet.js
- **Charts**: Chart.js
- **AI/ML**: TensorFlow (for predictive analytics and image recognition)
- **Real-time Communication**: Socket.IO for live capacity updates and alerts
- **QR Code Generation**: qrcode library for attendee check-in codes

## License

This project is licensed under the MIT License - see the LICENSE file for details.