from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

pref_table_triggered = False
alloc_comm_table_triggered = False
alloc_nocomm_table_triggered = False
updated_agent_areas = False
beep_triggered = False
total_score = 0
time_water = 0


PREFERENCES_CSV = "preferences.csv"

agent_areas = []
human_areas = []


def update_beep(beep_value):
    global beep_triggered
    beep_triggered = beep_value

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

@app.route('/check_updates', methods=['GET'])
def check_updates():
    global beep_triggered, total_score, time_water
    print("check beep", beep_triggered)
    return jsonify({"play_beep": beep_triggered, 
                    "total_score": total_score,
                    "time_water": time_water,
                    "human_areas": human_areas}), 200
     
    
@app.route('/close_allocation_nocomm', methods=['GET'])
def close_allocation_nocomm():
    global alloc_nocomm_table_triggered

    alloc_nocomm_table_triggered = False
    return jsonify({"status": "closed"}), 200
    
@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    global PREFERENCES_CSV
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
    
    
@app.route('/show_alloc', methods=['POST'])
def show_alloc():
    allocation = {}

    # Populate allocation from agent_areas (if any)
    if agent_areas:
        for area in agent_areas:
            allocation[f"p_{area}"] = "Artificial Agent"

    return jsonify({"alloc": allocation})
    
@app.route('/update_allocation_comm', methods=['POST'])
def update_allocation_comm():
    try:
        global agent_areas, human_areas, alloc_comm_table_triggered, updated_agent_areas
        data = request.get_json(force=True)
        print(data)

        agent_areas = data.get("agent_areas", [])
        human_areas = data.get("human_areas", [])

        print("areas table_api", agent_areas)

        alloc_comm_table_triggered = False
        updated_agent_areas = True

        return jsonify({"status": "updated"})
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