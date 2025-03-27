import os, requests
import sys
import csv
import glob
import pathlib
import threading
from SaR_gui import visualization_server
from worlds1.WorldBuilder import create_builder
from pathlib import Path
from loggers.OutputLogger import output_logger
from queue import Queue
import table_api
import argparse


if __name__ == "__main__":
    print("pref table triggered", table_api.pref_table_triggered)
    print("alloc with comm table triggered", table_api.alloc_comm_table_triggered)
    print("alloc without comm table triggered", table_api.alloc_nocomm_table_triggered)
    table_api.pref_table_triggered = False # TURN True for table to appear in the beginning - to fix later and move to the end of tutorial
    table_api.alloc_comm_table_triggered = False
    table_api.alloc_nocomm_table_triggered = False

    if (table_api.pref_table_triggered + table_api.alloc_comm_table_triggered + table_api.alloc_nocomm_table_triggered > 1):
        print("ONLY ONE TABLE SHOULD BE TRIGGERED AT A TIME")
        exit()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--condition', dest='condition', required=True, choices={"tutorial", "mission_comm", "mission_nocomm", "pref_table"}, type=str, help='Add condition: tutorial, mission_comm, mission_nocomm, or pref_table')
    parser.add_argument('--agent', dest='agent_type', required=False, default="tutorial",choices={"will","nowill"}, type=str, help="Add the agent type: tutorial, will or nowill.")
    parser.add_argument('--pid', dest='pid', required=False, default="0", type=str, help='Add participant ID')

    args = parser.parse_args()

    fld = os.getcwd()

    name = "Human"

    builder = create_builder(condition=args.condition, agent_type=args.agent_type, name=name, participant_id = args.pid, folder=fld)


    # Start overarching MATRX scripts and threads, such as the api and/or visualizer if requested. Here we also link our own media resource folder with MATRX.
    media_folder = pathlib.Path().resolve()
    builder.startup(media_folder=media_folder)
    print("Starting custom visualizer")
    vis_thread = visualization_server.run_matrx_visualizer(verbose=False, media_folder=media_folder)
    world = builder.get_world()
    print("Started world...")
    print(str(visualization_server.port))
    builder.api_info['matrx_paused'] = True

    # Run Flask server in a separate thread
    flask_thread = threading.Thread(target=table_api.run_table_flask)
    flask_thread.start()


    world.run(builder.api_info)
    print("DONE!")
    print("Shutting down custom visualizer")
    r = requests.post("http://localhost:" + str(visualization_server.port) + "/shutdown_visualizer")
    vis_thread.join(timeout=5)
    #if task_type=="mission":
        # Generate one final output log file for the official task type
    #    output_logger(fld)
    builder.stop()
