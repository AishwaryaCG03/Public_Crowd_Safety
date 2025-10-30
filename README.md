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
4. Set up environment variables in a `.env` file:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URI=sqlite:///site.db
   ```
5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
6. Run the application:
   ```
   flask run
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

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Maps**: Leaflet.js
- **Charts**: Chart.js
- **AI/ML**: TensorFlow (for predictive analytics and image recognition)

## License

This project is licensed under the MIT License - see the LICENSE file for details.