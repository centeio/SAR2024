from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

communication_triggered = False
preference_data = "nothing"

# Serve static files from the 'images' directory
@app.route('/images/<path:filename>')
def serve_image(filename):
    # Serve the image from the 'images' directory
    return send_from_directory('images', filename)

@app.route('/trigger_communication', methods=['GET'])
def trigger_communication():
    global communication_triggered
    communication_triggered = True
    return jsonify({"status": "triggered"}), 200

@app.route('/check_communication', methods=['GET'])
def check_communication():
    global communication_triggered
    if communication_triggered:
        return jsonify({"show_communication": True}), 200
    else:
        return jsonify({"show_communication": False}), 200
    
@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    print("here update preferences")
    global preference_data, communication_triggered
    data = request.get_json(force=True)
    print("json data", data)
    preference_data = data["test_value"]
    print("preference data", preference_data)
    communication_triggered = False
    return jsonify({"status": "updated"}), 200

@app.route('/update_status', methods=['POST'])
def update_status():
    global status_data
    data = request.get_json()
    status_data["collected_victims"] = data.get("collected_victims", [])
    status_data["searched_rooms"] = data.get("searched_rooms_robot", [])
    status_data["searched_rooms_human"] = data.get("searched_rooms_human", [])
    status_data["trust_impact_list"] = data.get("trust_impact_list", [])
    status_data["trust_per_task"] = data.get("trust_per_task", {})
    status_data["confidence_per_task"] = data.get("confidence_per_task", {})
    return jsonify({"status": "updated"}), 200

@app.route('/update_time', methods=['POST'])
def update_time():
    global status_data
    data = request.get_json()
    status_data["elapsed_time"] = data.get("time", None)
    return jsonify({"status": "updated"}), 200

@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(status_data), 200

# Function to run the Flask server in a separate thread
def run_table_flask():
    print("Starting Flask server")
    app.run(port=5001)