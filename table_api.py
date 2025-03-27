from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

pref_table_triggered = False
alloc_comm_table_triggered = False
alloc_nocomm_table_triggered = False
PREFERENCES_CSV = "preferences.csv"

beep_triggered = False

def update_beep(beep_value):
    global beep_triggered
    print("BEEEEP", beep_value)
    beep_triggered = beep_value

# Ensure CSV file has headers
with open(PREFERENCES_CSV, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["p_id", "preference", "preference_num"])


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
    global pref_table_triggered, alloc_comm_table_triggered, alloc_nocomm_table_triggered
    print("check comm", pref_table_triggered, alloc_comm_table_triggered, alloc_nocomm_table_triggered)
    return jsonify({"show_pref_table": pref_table_triggered,
                    "show_alloc_comm": alloc_comm_table_triggered,
                    "show_alloc_nocomm": alloc_nocomm_table_triggered}), 200

@app.route('/check_beep', methods=['GET'])
def check_beep():
    global beep_triggered
    print("check beep", beep_triggered)
    if beep_triggered:
        return jsonify({"play_beep": True}), 200
    else:
        return jsonify({"play_beep": False}), 200   

    
@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    try:
        print("here update preferences")
        global pref_table_triggered
        data = request.get_json(force=True)
        if not isinstance(data, list):
            return jsonify({"error": "Invalid data format, expected a list"}), 400
        print("json data", data)
        # Define mapping of preference to numeric value
        preference_map = {f"willing_{i}": i for i in range(1, 10)}  # Supports willing_1 to willing_9
        
        # Process each row's preference
        with open(PREFERENCES_CSV, mode='a', newline='') as file:
            writer = csv.writer(file)
            for entry in data:
                row_id = entry.get("id")
                preference = entry.get("preference")
                
                if row_id is None or preference is None:
                    return jsonify({"error": "Missing id or preference in data"}), 400
                
                preference_num = preference_map.get(preference, 0)  # Default to 0 if not found
                writer.writerow([row_id, preference, preference_num])
                print("endline",row_id, preference, preference_num)
            print("end file")

        pref_table_triggered = False
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/update_allocation_nocomm', methods=['POST'])
def update_allocation_nocomm():
    try:
        global alloc_nocomm_table_triggered
        data = request.get_json(force=True)
        # TODO actually update tasks
        print(data)
        alloc_nocomm_table_triggered = False
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/update_allocation_comm', methods=['POST'])
def update_allocation_comm():
    try:
        data = request.get_json(force=True)
        global alloc_comm_table_triggered
        # TODO actually update tasks
        alloc_comm_table_triggered = False
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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