// data on the MATRX API
var matrx_url = 'http://' + window.location.hostname,
    port = "3001",
    matrx_send_message_url = "send_message";


/*********************************************************************
 * Simulation control buttons in toolbar (start/pause etc.)
 ********************************************************************/


// Toolbar elements
var start_button = document.getElementById("start_button"),
    pause_button = document.getElementById("pause_button"),
    stop_button = document.getElementById("stop_button");


/**
 * Synchronizes the play/pause button with the current value of MATRX
 */
function sync_play_button(matrx_paused) {

    console.log("syncing play/pause button, matrx_paused:", matrx_paused);
    // hide the play button and show the pause button
    if (!matrx_paused) {
        start_button.classList.add("hidden");
        pause_button.classList.remove("hidden");

        // vice versa
    } else {
        start_button.classList.remove("hidden");
        pause_button.classList.add("hidden");
    }
}

start_button.addEventListener("click", toggle_start, false);

function toggle_start() {
    console.log("pressed play");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("start");
}

pause_button.addEventListener("click", toggle_pause, false);

function toggle_pause() {
    console.log("pressed pause");
    // hide / unhide the correct button
    start_button.classList.toggle("hidden");
    pause_button.classList.toggle("hidden");

    // send API message to MATRX
    send_api_message("pause");
}


stop_button.addEventListener("click", toggle_stop, false);

function toggle_stop() {
    send_api_message("stop");
}


/**
 * Send a message to the MATRX API
 */
function send_api_message(type) {
    var resp = $.ajax({
        method: "GET",
        url: matrx_url + ":" + port + "/" + type,
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    });
}

function send_matrx_api_post_message(type, post_data) {
    var resp = $.ajax({
        method: "POST",
        data: JSON.stringify(post_data),
        url: matrx_url + ":" + port + "/" + type,
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    });
}

/*********************************************************************
 * Agent menu
 ********************************************************************/

/**
 * Populate the menu with links to the views of all agents
 */
function populate_agent_menu(state) {
    agents = [];
    var dropdown = document.getElementById("agent_dropdown");

    // remove old agents
    while (dropdown.firstChild) {
        dropdown.removeChild(dropdown.firstChild);
    }


    // search for agents
    var objects_keys = Object.keys(state);
    objects_keys.forEach(function(objID) {
        // don't list ourselves
        if (objID == lv_agent_id) {
            return;
        }

        // fetch agent object from state
        var obj = state[objID];

        // save the agent
        if (obj.hasOwnProperty('isAgent')) {
            agents.push(obj);
        }
    })

    // show what the agent looks like
    agents.forEach(function(agent) {
        var agentType = agent["is_human_agent"] ? "human-agent" : "agent";

        // preview of the agent
        var agent_preview = document.createElement("div");
        agent_preview.classList.add("agent_menu_preview");

        // use the image as the agent preview
        if (Object.keys(agent).includes('img_name')) {
            var img = new Image();
            img.src = window.location.origin + fix_img_url(agent['img_name']);
            agent_preview.append(img);

            // otherwise, use the the agent shape and colour as a preview
        } else {

            // add the css for the corresponding agent shape
            switch (agent['visualization']['shape']) {
                case 0:
                    agent_preview.setAttribute("style", "background-color: " + agent['visualization']['colour'] + ';');
                    break;
                case 2:
                    agent_preview.setAttribute("style", 'background-color:' + agent['visualization']['colour'] + '; border-radius: 100%');
                    break;
                case 1:
                    agent_preview.setAttribute("style", 'width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent;border-bottom: 24px solid' + agent['visualization']['colour'] + ';');
                    break;
            }
        }

        // create a new dropdown item and add the preview and agent name
        var list_item = document.createElement('a');
        list_item.classList.add('dropdown-item');
        list_item.append(agent_preview);
        list_item.appendChild(document.createTextNode(agentType + ": " + agent["obj_id"]));
        list_item.href = '/' + agentType + '/' + agent["obj_id"]
        list_item.setAttribute('target', '_blank'); // open in a new tab

        // add the agent to the dropdown list
        dropdown.append(list_item);
    });
}

/*********************************************************************
 * Drawing tools
 ********************************************************************/
// Called when draw button is clicked. Enables/disables draw function
var draw_activated = false;

// Called when erase button is clicked. Enables/disables erase function
var erase_activated = false;

/*
 * Change class of all tiles so that they are highlighted when hovered
 */
function add_draw_erase_classes(class_name) {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].className = "tile " + class_name;
    }
    var objects = document.getElementsByClassName("object");
    for (var i = 0; i < objects.length; i++) {
        objects[i].className = "object " + class_name;
    }
}

/*
 * Change class of all tiles so that they are no longer highlighted when hovered
 */
function remove_draw_erase_classes() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].className = "tile";
    }
    var objects = document.getElementsByClassName("object");
    for (var i = 0; i < objects.length; i++) {
        objects[i].className = "object";
    }
}

/*
 * Toggle drawing mode when the button is pressed
 */
function drawToggle() {
    if (erase_activated) { // If the erase function is active, disable it
        eraseToggle();
    }
    draw_activated = !draw_activated;
    if (draw_activated) {
        document.getElementById("draw_button").className = "btn btn-secondary";
        add_draw_erase_classes("draw_mode");
    } else {
        document.getElementById("draw_button").className = "btn btn-dark";
        remove_draw_erase_classes();
    }
}

/*
 * Toggle erase mode when the button is pressed
 */
function eraseToggle() {
    if (draw_activated) { // If the draw function is active, disable it
        drawToggle();
    }
    erase_activated = !erase_activated;
    if (erase_activated) {
        document.getElementById("erase_button").className = "btn btn-secondary";
        add_draw_erase_classes("erase_mode");
    } else {
        document.getElementById("erase_button").className = "btn btn-dark";
        remove_draw_erase_classes();
    }
}

/*
 * Called when a tile is clicked. Draws/erases the tile and starts drag function that allows the
 * user to draw/erase multiple tiles while holding the left mouse button
 */
function startDrawErase(tile_id) {
    if (draw_activated) {
        drawTile(tile_id);
        startDrawDrag();
    }
    if (erase_activated) {
        eraseTile(tile_id);
        startEraseDrag();
    }
}

/*
 * Determines what happens when a tile is selected for drawing / erasing
 */
function drawTile(tile_id) {
    if (draw_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "crimson";
    }
}

/*
 * Sets mouse event listeners for drawing  by dragging the mouse
 */
function startDrawDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "drawTile(id)");
    }
}

/*
 * Remove the mouse listeners for drawing / erasing by dragging the mouse
 */
function stopDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "");
    }
}

/*
 * Determine what happens when a tile is clicked for erasing
 */
function eraseTile(tile_id) {
    if (erase_activated) {
        var tile = document.getElementById(tile_id);
        tile.style.backgroundColor = "";
    }
}

/*
 * Sets mouse event listeners for erasing by dragging the mouse
 */
function startEraseDrag() {
    var tiles = document.getElementsByClassName("tile");
    for (var i = 0; i < tiles.length; i++) {
        tiles[i].setAttribute("onmouseenter", "eraseTile(id)");
    }
}