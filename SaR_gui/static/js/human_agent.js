/*
 * This file handles keypresses and sends them back to the MATRX server
 */

var close_table_btn = document.getElementById("close_table_btn");


$(document).ready(function() {
    // bind key listener
    document.onkeydown = check_arrow_key;
});


/**
 * Catch user pressed keys with arrow keys
 *
 */
function check_arrow_key(e) {
    e = e || window.event;

    // ignore the event if the user is writing in the message input field
    if (document.getElementById("chat_form_input") === document.activeElement) {
        return
    }

//    console.log("Userinput:", e);

    data = [e.key];

    send_userinput_to_MATRX(data);
}




function select_agent(e) {


}


close_table_btn.addEventListener("click", close_table, false);

function close_table() {
  fetch('http://localhost:5001/update_preferences', {
        method: 'POST',
        body: JSON.stringify({ test_value: "example" })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'updated') {
            document.getElementById('overlay').style.display = 'none';
            console.log("preferences updated")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to clear trust impact list:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}

function showCommunication() {
    document.getElementById('overlay').style.display = 'flex';
    toggle_pause(); // Pause the game when the overlay is shown
}

function hideCommunication() {
    fetch('http://localhost:5001/clear_after_summary', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'cleared') {
            console.log("close table")
            document.getElementById('overlay').style.display = 'none';
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to clear trust impact list:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}
function checkCommunication() {
    fetch('http://localhost:5001/check_communication')
        .then(response => response.json())
        .then(data => {
            console.log("show communication")
            console.log(data.show_communication)
            if (data.show_communication) {
              showCommunication();
            }
        })
        .catch(error => console.error('Error checking communication:', error));
}

setInterval(checkCommunication, 1000);
