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

if __name__ == "__main__":
    print("communication triggered", table_api.communication_triggered)
    table_api.communication_triggered = False # TURN True for table to appear in the beginning - to fix later and move to the end of tutorial
    fld = os.getcwd()
    #print("\nEnter one of the task types 'tutorial' or 'official':")
    #choice1=input()
    #print("\nEnter a name or id for the human agent:")
    #choice2=input()
    #if choice1=='mission':
    task_type = "mission"
    condition = "mission"
    name = "caro"
    participant_id = 0

    builder = create_builder(task_type='mission',condition='mission', name=name, participant_id = participant_id, folder=fld)


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
