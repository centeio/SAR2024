from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv, time, os
import pandas as pd
from werkzeug.serving import make_server
import threading

# Initialize Flask app
port = 5001
table_app = Flask(__name__, static_folder='static')
CORS(table_app)

pref_table_triggered = False
alloc_comm_table_triggered = False
alloc_nocomm_table_triggered = False
updated_agent_areas = False
beep_triggered = False
total_score = 0
time_water = 0
start_time = 0
total_time = 0
completeness = 0
human_vics_saved_abs = 0
agent_vics_saved_abs = 0
agent_vics_saved_by_human_abs = 0
human_vics_in_order = 0
agent_name = ""

# PID	final_score	final_completeness	human_vics_saved_abs	human_vics_saved_rel	agent_vics_saved_abs	agent_vics_saved_rel	agent_vics_saved_by_human_abs	agent_vics_saved_by_human_rel	compliance = human_vics_saved/(human_vics_saved + agent_vics_saved_by_human)	water_time	game_time	human_vics_in_order	

FOLDER_ID = ""
PREFERENCES_CSV = ""
ALLOCATION_CSV = ""
ACTIONS_CSV = ""
FINAL_CSV = ""

agent_areas = []
human_areas = []

action_logs =  pd.DataFrame(columns = ["condition","PID","agent_type","tick","local_time","location","vic_area","in_own_area?","action","victim","vic_drop_loc","vic_order","score","completeness","water_time"])
allocation_log = pd.DataFrame(columns = ["condition","agent_type","PID","area","agent_assignment","change?"])

def update_beep(beep_value):
    global beep_triggered
    beep_triggered = beep_value

def log_final_output(participant_id, condition, agent_type, agent_name):
    # Column order
    final_logs = pd.DataFrame([{
        "PID": participant_id,
        "condition": condition,
        "agent_type": agent_type,
        "agent_name": agent_name,
        "final_score": total_score,
        "final_completeness": completeness,
        "human_vics_saved_abs": human_vics_saved_abs,
        "human_vics_saved_rel": human_vics_saved_abs / (2.0*4), #number of victims times the areas
        "agent_vics_saved_abs": agent_vics_saved_abs,
        "agent_vics_saved_rel": agent_vics_saved_abs / (2.0*4),
        "agent_vics_saved_by_human_abs": agent_vics_saved_by_human_abs,
        "agent_vics_saved_by_human_rel": agent_vics_saved_by_human_abs / (2.0*4),
        "compliance": human_vics_saved_abs/(human_vics_saved_abs + agent_vics_saved_by_human_abs),
        "water_time": time_water,
        "game_time": total_time,
        "human_vics_in_order": human_vics_in_order
    }])

    if os.path.exists(FINAL_CSV):
        # Append to the file without writing the header
        final_logs.to_csv(FINAL_CSV, mode='a', header=False, index=False)
    else:
        final_logs.to_csv(FINAL_CSV, mode='w', header=True, index=False)




# Serve static files from the 'images' directory
@table_app.route('/images/<path:filename>')
def serve_image(filename):
    # Serve the image from the 'images' directory
    return send_from_directory('images', filename)

@table_app.route('/trigger_communication', methods=['GET'])
def trigger_communication():
    global communication_triggered
    communication_triggered = True
    return jsonify({"status": "triggered"}), 200

@table_app.route('/check_communication', methods=['GET'])
def check_communication():
    global pref_table_triggered, alloc_comm_table_triggered, alloc_nocomm_table_triggered, agent_name
    #print("check comm", pref_table_triggered, alloc_comm_table_triggered, alloc_nocomm_table_triggered)
    return jsonify({"show_pref_table": pref_table_triggered,
                    "show_alloc_comm": alloc_comm_table_triggered,
                    "show_alloc_nocomm": alloc_nocomm_table_triggered,
                    "agent_name": agent_name}), 200

@table_app.route('/check_updates', methods=['GET'])
def check_updates():
    global beep_triggered, total_score, time_water
    #print("check beep", beep_triggered)
    return jsonify({"play_beep": beep_triggered, 
                    "total_score": total_score,
                    "time_water": time_water,
                    "human_areas": human_areas}), 200
    
@table_app.route('/close_allocation_nocomm', methods=['GET'])
def close_allocation_nocomm():
    global alloc_nocomm_table_triggered

    alloc_nocomm_table_triggered = False
    return jsonify({"status": "closed"}), 200
    
@table_app.route('/update_preferences', methods=['POST'])
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
                #print("endline",row_id, preference, preference_num)
            #print("end file")

        pref_table_triggered = False
        return jsonify({"status": "updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@table_app.route('/show_alloc', methods=['POST'])
def show_alloc():
    allocation = {}

    # Populate allocation from agent_areas (if any)
    if agent_areas:
        for area in agent_areas:
            allocation[f"p_{area}"] = "Artificial Agent"

    return jsonify({"alloc": allocation})
    
@table_app.route('/update_allocation_comm', methods=['POST'])
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
    

@table_app.route('/update_time', methods=['POST'])
def update_time():
    global status_data
    data = request.get_json()
    status_data["elapsed_time"] = data.get("time", None)
    return jsonify({"status": "updated"}), 200

@table_app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(status_data), 200

# Function to run the Flask server in a separate thread
def run_table_flask():
    global port
    print("Starting Flask server")
    
    # Create a server instance using make_server
    server = make_server('0.0.0.0', port, table_app)
    
    # Store the server reference in app, so it can be accessed elsewhere for shutdown
    table_app.table_server = server

    # Start serving the Flask app
    server.serve_forever()

@table_app.route('/shutdown_table_api', methods=['POST'])
def shutdown_table_api():
    """ Shuts down the table API server by calling its shutdown method """
    try:
        # Shutdown the server in a separate thread to avoid blocking
        threading.Thread(target=table_app.table_server.shutdown).start()
        return "Table API server shutting down..."
    except Exception as e:
        return f"Error during shutdown: {str(e)}"