from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/health')
def health():
    return jsonify(status="MCP Server Running ✅")

# Route triggered when UI wants crowd prediction
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    event_id = data['eventId']

    # Call AI model / ML script on your machine
    ai_response = requests.post("http://127.0.0.1:5001/predict", json=data)

    # Send result to connected clients (dashboard)
    socketio.emit('crowdPrediction', ai_response.json(), room=event_id)
    return jsonify(success=True)

# SocketIO connection for live event monitoring
@socketio.on('joinEvent')
def on_join(data):
    join_room(data['eventId'])

@socketio.on('sensorUpdate')
def sensor_update(data):
    emit('sensorUpdate', data, room=data['eventId'])



if __name__ == "__main__":
    print("✅ MCP Server is running on port 3000...")
    socketio.run(app, port=3000, debug=True)

