import os, requests
import sys
import csv
import glob
import pathlib
import threading
from SaR_gui import visualization_server
from worlds1.WorldBuilder import create_builder
from pathlib import Path
from queue import Queue
import table_api
import argparse
import time
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--condition', dest='condition', required=True, choices={"tutorial", "mission_comm", "mission_nocomm", "pref_table"}, type=str, help='Add condition: tutorial, mission_comm, mission_nocomm, or pref_table')
    parser.add_argument('--agent_type', dest='agent_type', required=False, default="tutorial",choices={"will","nowill"}, type=str, help="Add the agent type: tutorial, will or nowill.")
    parser.add_argument('--pid', dest='pid', required=False, default="0", type=str, help='Add participant ID')
    parser.add_argument('--agent_name', dest='agent_name', required=False, choices={"Argo","Bolt"}, default="Argo", type=str, help="Add agent's name: Argo or Bolt")


    args = parser.parse_args()

    fld_name = os.getcwd() + "/logs/" + args.pid

    isFolder = os.path.exists(fld_name)
    if not isFolder:
        # Create a new directory because it does not exist
        os.makedirs(fld_name)
        print("The new directory is created!")

    name = "Human"

    table_api.pref_table_triggered = False
    table_api.alloc_comm_table_triggered = False
    table_api.alloc_nocomm_table_triggered = False

    table_api.agent_name = args.agent_name

    table_api.FOLDER_ID = fld_name
    table_api.PREFERENCES_CSV = fld_name + "/preferences.csv"
    table_api.ALLOCATION_CSV = fld_name + "/allocation.csv"
    table_api.ACTIONS_CSV = fld_name + "/actions.csv"
    table_api.FINAL_CSV = fld_name + "/final.csv"

    if args.condition == "pref_table":
        table_api.pref_table_triggered = True
        args.condition = "tutorial"
    elif args.condition == "mission_comm":
        table_api.alloc_comm_table_triggered = True
    elif args.condition == "mission_nocomm":
        table_api.alloc_nocomm_table_triggered = True

    if (table_api.pref_table_triggered + table_api.alloc_comm_table_triggered + table_api.alloc_nocomm_table_triggered > 1):
        print("ONLY ONE TABLE SHOULD BE TRIGGERED AT A TIME")
        exit()

    table_api.start_time = time.time()
    builder = create_builder(condition=args.condition, agent_type=args.agent_type, agent_name=args.agent_name, name=name, participant_id = args.pid, folder=fld_name)


    # Start overarching MATRX scripts and threads, such as the api and/or visualizer if requested. Here we also link our own media resource folder with MATRX.
    media_folder = pathlib.Path().resolve()
    builder.startup(media_folder=media_folder)

    print("Starting custom visualizer")
    vis_thread = threading.Thread(
        target=visualization_server.run_matrx_visualizer,
        args=(False, media_folder)
    )
    vis_thread.start()
    #vis_thread = visualization_server.run_matrx_visualizer(verbose=False, media_folder=media_folder)

    world = builder.get_world()
    print("Started world...")
    print(str(visualization_server.port))

    builder.api_info['matrx_paused'] = True

    # Run Flask server in a separate thread
    flask_thread = threading.Thread(target=table_api.run_table_flask)
    flask_thread.start()


    world.run(builder.api_info)

    table_api.total_time = time.time() - table_api.start_time

    # LOG ACTIONS
    try:
        if args.condition == "mission_comm" or args.condition == "mission_nocomm":
            if os.path.exists(table_api.ACTIONS_CSV):
            # Append to the file without writing the header
                table_api.action_logs.to_csv(table_api.ACTIONS_CSV, mode='a', header=False, index=False)
            else:
                # If the file does not exist, write the DataFrame with the header
                table_api.action_logs.to_csv(table_api.ACTIONS_CSV, mode='w', header=True, index=False)
        
            # LOG FINAL
            table_api.log_final_output(participant_id = args.pid, condition=args.condition, agent_type=args.agent_type, agent_name = args.agent_name)
    
    except Exception as e:
        print(f"Error while logging: {e}")



    r1 = requests.post("http://localhost:" + str(table_api.port) + "/shutdown_table_api")
    flask_thread.join()
    print("Table API thread stopped")

    print("Now shutting down custom visualizer")
    r2 = requests.post("http://localhost:" + str(visualization_server.port) + "/shutdown_visualizer")
    vis_thread.join(timeout=5)
    print("Visualizer thread stopped")

    builder.stop()
