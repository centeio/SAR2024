import threading
import logging
import os
import signal
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.serving import make_server


'''
This file holds the code for the MATRX RESTful api. 
External scripts can send POST and/or GET requests to retrieve state, tick and other information, and send 
userinput or other information to MATRX. The api is a Flask (Python) webserver.

For visualization, see the seperate MATRX visualization folder / package.
'''

debug = False
port = 8000
app = Flask(__name__, template_folder='templates')

# the path to the media folder of the user (outside of the MATRX package)
ext_media_folder = ""

#########################################################################
# Visualization server routes
#########################################################################

@app.route('/human-agent/<id>')
def human_agent_view(id):
    """
    Route for HumanAgentBrain

    Parameters
    ----------
    id
        The human agent ID. Is obtained from the URL.

    Returns
    -------
    str
        The template for this agent's view.

    """
    return render_template('human_agent.html', id=id)


# route for agent, get the ID from the URL
@app.route('/agent/<id>')
def agent_view(id):
    """
    Route for AgentBrain

    Parameters
    ----------
    id
        The agent ID. Is obtained from the URL.

    Returns
    -------
    str
        The template for this agent's view.

    """
    return render_template('agent.html', id=id)


@app.route('/god')
def god_view():
    """
    Route for the 'god' view which contains the ground truth of the world without restrictions.

    Returns
    -------
    str
        The template for this view.

    """
    return render_template('god.html')


@app.route('/')
@app.route('/start')
def start_view():
    """
    Route for the 'start' view which shows information about the current scenario, including links to all agents.

    Returns
    -------
    str
        The template for this view.

    """
    return render_template('start.html')




@app.route('/shutdown_visualizer', methods=['POST'])
def shutdown():
    """ Gracefully shuts down the visualizer server """
    try:
        # Shutdown the server in a separate thread to avoid blocking
        threading.Thread(target=app.visualizer_server.shutdown).start()
        return "Visualizer server shutting down..."
    except Exception as e:
        return f"Error during visualizer shutdown: {str(e)}"


@app.route('/fetch_external_media/<path:filename>')
def external_media(filename):
    """ Facilitate the use of images in the visualization outside of the static folder

    Parameters
    ----------
    filename
        path to the image file in the external media folder of the user.

    Returns
    -------
        Returns the url (relative from the website root) to that file
    """
    return send_from_directory(ext_media_folder, filename, as_attachment=True)


#########################################################################
# Visualization Flask methods
#########################################################################

def _flask_thread():
    """
    Starts the Flask server on localhost:3000
    """

    if not debug:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_matrx_visualizer(verbose, media_folder):
    """
    Creates a seperate Python thread in which the visualization server (Flask) is started, serving the JS visualization
    :return: MATRX visualization Python thread
    """
    global debug, ext_media_folder, s
    debug = verbose
    ext_media_folder = media_folder

    print("Starting visualization server")
    print("Initialized app:", app)
    s = make_server('0.0.0.0', port, app)

    app.visualizer_server = s

    s.serve_forever()

if __name__ == "__main__":
    run_matrx_visualizer()
