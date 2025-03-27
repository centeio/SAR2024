/*
 * This file handles keypresses and sends them back to the MATRX server
 */

var close_pref_table_btn = document.getElementById("close_pref_table_btn");
var close_alloc_comm_table_btn = document.getElementById("close_alloc_comm_btn");
var close_alloc_nocomm_table_btn = document.getElementById("close_alloc_nocomm_btn");


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


close_pref_table_btn.addEventListener("click", close_pref_table, false);
close_alloc_comm_table_btn.addEventListener("click", close_alloc_comm_table, false);
close_alloc_nocomm_table_btn.addEventListener("click", close_alloc_nocomm_table, false);


function close_alloc_nocomm_table() {
    fetch('http://localhost:5001/update_allocation_nocomm', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify("table closed")
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'updated') {
            document.getElementById('alloc_nocomm_overlay').style.display = 'none';
            console.log("allocation table closed")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to update task allocation trigger:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}

function close_alloc_comm_table() {
    const table = document.getElementById("alloc_table_comm");
    const dropdowns = table.querySelectorAll("select");

    let preferences = [];
    dropdowns.forEach(dropdown => {
        let row = dropdown.closest("tr");
        let rowId = row.getAttribute("data-id"); // Assuming each row has a unique identifier
        let selectedValue = dropdown.value;
        
        preferences.push({ id: rowId, preference: selectedValue });
    });
    fetch('http://localhost:5001/update_allocation_comm', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(preferences)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'updated') {
            document.getElementById('alloc_comm_overlay').style.display = 'none';
            console.log("allocation updated")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to update task allocation:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}

function close_pref_table() {
    const table = document.getElementById("pref_table");
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
            document.getElementById('pref_overlay').style.display = 'none';
            console.log("preferences updated")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to update preferences:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}

function showPrefTable() {
    document.getElementById('pref_overlay').style.display = 'flex';
    toggle_pause(); // Pause the game when the overlay is shown
}

function showAllocComm() {
    document.getElementById('alloc_comm_overlay').style.display = 'flex';
    toggle_pause(); // Pause the game when the overlay is shown
}

function showAllocNoComm() {
    document.getElementById('alloc_nocomm_overlay').style.display = 'flex';
    toggle_pause(); // Pause the game when the overlay is shown
}

function checkCommunication() {
    fetch('http://localhost:5001/check_communication')
        .then(response => response.json())
        .then(data => {
            if (data.show_pref_table) {
                console.log("show preff table")
                showPrefTable();
            };
            if (data.show_alloc_comm) {
                console.log("show allocation table with comm")
                showAllocComm();
            }
            if (data.show_alloc_nocomm) {
                console.log("show allocation table without comm")
                showAllocNoComm();
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
            console.log(data.play_beep)
            if (data.play_beep) {
                playBeep();
            }
        })
        .catch(error => console.error('Error checking beep:', error));    

}

setInterval(checkCommunication, 500);
setInterval(checkBeep, 500);
