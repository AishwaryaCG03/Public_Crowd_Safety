from flask import Flask
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO

load_dotenv()  # Load environment variables from .env if present
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins="*")

# Import routes at the bottom to avoid circular imports
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Run with SocketIO to enable WebSocket transport
    socketio.run(app, debug=True)