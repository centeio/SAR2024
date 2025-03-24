/*
 * This file handles keypresses and sends them back to the MATRX server
 */

var close_table_btn = document.getElementById("close_table_btn");

const beep_sound = new Audio("https://www.soundjay.com/buttons/sounds/beep-08b.mp3");


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
    const table = document.getElementById("preferencesTable");
    const dropdowns = table.querySelectorAll("select");

    let preferences = [];
    dropdowns.forEach(dropdown => {
        let row = dropdown.closest("tr");
        let rowId = row.getAttribute("data-id"); // Assuming each row has a unique identifier
        let selectedValue = dropdown.value;
        
        preferences.push({ id: rowId, preference: selectedValue });
    });
    fetch('http://localhost:5001/update_preferences', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(preferences)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'updated') {
            document.getElementById('overlay').style.display = 'none';
            console.log("preferences updated")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to update preferences:', data.reason);
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
            console.log("show communication?")
            console.log(data.show_communication)
            if (data.show_communication) {
              showCommunication();
            }
        })
        .catch(error => console.error('Error checking communication:', error));
}

function playBeep() {
    beep_sound.play()
}

function checkBeep() {
    fetch('http://localhost:5001/check_beep')
        .then(response => response.json())
        .then(data => {
            console.log("play beep?")
            console.log(data.play_beep)
            if (data.play_beep) {
                playBeep();
            }
        })
        .catch(error => console.error('Error checking beep:', error));    

}

setInterval(checkCommunication, 1000);
setInterval(checkBeep, 1000);
