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
    fetch('http://localhost:5001/close_allocation_nocomm')
    .then(response => response.json())
    .then(data => {
        if (data.status === 'closed') {
            document.getElementById('alloc_nocomm_overlay').style.display = 'none';
            console.log("allocation table closed")
            toggle_start(); // Start or resume the game when the overlay is hidden
        } else {
            console.error('Failed to close task allocation table:', data.reason);
        }
    })
    .catch(error => console.error('Error sending clear signal:', error));
}

function close_alloc_comm_table() {
    const table = document.getElementById("alloc_table_comm");
    const dropdowns = table.querySelectorAll("select");
    const overlay = document.getElementById("alloc_comm_overlay");

    // Build the updated allocation based on the user's choices
    let updatedAllocation = {
        agent_areas: [],
        human_areas: []
    };

    dropdowns.forEach(dropdown => {
        let row = dropdown.closest("tr");
        let rowId = row.getAttribute("data-id"); // e.g., "p_A1"
        let selectedValue = dropdown.value;

        let area = rowId.replace("p_", ""); // Extract just "A1" from "p_A1"

        if (selectedValue === "Artificial Agent") {
            updatedAllocation.agent_areas.push(area);
        }
        if (selectedValue === "Human Teammate") {
            updatedAllocation.human_areas.push(area);
        }
    });

    // Validation: Check if each has exactly 4 areas
    if (updatedAllocation.agent_areas.length !== 4 || updatedAllocation.human_areas.length !== 4) {
        // Find or create the error message
        let errorMsg = document.getElementById("alloc_comm_error_msg");

        if (!errorMsg) {
            errorMsg = document.createElement("div");
            errorMsg.id = "alloc_comm_error_msg";
            errorMsg.style.color = "red";
            errorMsg.style.marginTop = "10px";
            errorMsg.style.textAlign = "center";
            errorMsg.textContent = "Please select four areas for each team member.";

            // Append it directly under the table
            table.parentNode.insertBefore(errorMsg, table.nextSibling);
        } else {
            errorMsg.textContent = "Please select four areas for each team member.";
        }
        return; // Stop the function here, but keep the overlay open for updates
    }

    // Clear any existing error message if the validation passes
    const existingError = document.getElementById("alloc_comm_error_msg");
    if (existingError) {
        existingError.remove();
    }

    // Send updated allocation to the backend
    fetch('http://localhost:5001/update_allocation_comm', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(updatedAllocation)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'updated') {
            // Only close the overlay when the allocation is successfully updated
            document.getElementById('alloc_comm_overlay').style.display = 'none';
            console.log("Allocation updated successfully");
            toggle_start(); // Resume the game
        } else {
            console.error('Failed to update task allocation:', data.reason);
        }
    })
    .catch(error => console.error('Error sending allocation update:', error));
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

function showAlloc(comm) {
    fetch('http://localhost:5001/show_alloc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ comm: comm })
    })
    .then(response => response.json())
    .then(data => {
        const allocData = data.alloc;

        // Don't proceed if allocation data is empty
        if (!allocData || Object.keys(allocData).length === 0) {
            console.warn('Allocation data is empty.');
            return;
        }

        const overlayId = comm ? 'alloc_comm_overlay' : 'alloc_nocomm_overlay';
        const tableId = comm ? 'alloc_table_comm' : 'alloc_table_nocomm';
        const table = document.getElementById(tableId);

        const rows = table.querySelectorAll('tr[data-id]');

        rows.forEach(row => {
            // Skip if already marked as updated
            if (row.dataset.updated === "true") return;

            const taskId = row.getAttribute('data-id');
            const assignedTo = allocData[taskId] || 'Human Teammate';

            if (comm) {
                const select = row.querySelector('select');
                if (select) {
                    select.value = assignedTo;
                }
            } else {
                const cells = row.querySelectorAll('td');
                if (cells.length > 1) {
                    cells[1].textContent = assignedTo;
                }
            }

            // Mark this row as updated so we don't override it again
            row.dataset.updated = "true";
        });

        // Show the correct overlay
        document.getElementById(overlayId).style.display = 'flex';
        toggle_pause(); // Pause the game
    })
    .catch(error => console.error('Error fetching allocation data:', error));
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
                showAlloc(true);
            }
            if (data.show_alloc_nocomm) {
                console.log("show allocation table without comm")
                showAlloc(false);
            }        
        })
        .catch(error => console.error('Error checking communication:', error));
}

function playBeep() {
    beep_sound.play()
}

function checkUpdates() {
    fetch('http://localhost:5001/check_updates')
        .then(response => response.json())
        .then(data => {
            console.log(data.play_beep);

            // Play beep if triggered
            if (data.play_beep) {
                playBeep();
            }

            // Update score
            const scoreDiv = document.getElementById('score');
            if (scoreDiv) {
                scoreDiv.textContent = `Score: ${data.total_score};`;
            }

            // Convert time_water from seconds to mm:ss
            const minutes = Math.floor(data.time_water / 60);
            const seconds = Math.floor(data.time_water % 60);
            const formattedTime = `${minutes}m ${seconds.toString().padStart(2, '0')}s`;

            // Update water time
            const waterTimeDiv = document.getElementById('water_time');
            if (waterTimeDiv) {
                waterTimeDiv.textContent = `Time in water: ${formattedTime}`;
            }

            // Update tasks (human_areas)
            const tasksDiv = document.getElementById('tasks');
            if (tasksDiv && Array.isArray(data.human_areas)) {
                const taskList = data.human_areas.join(', ');
                tasksDiv.textContent = `Human tasks: ${taskList}`;
            }

        })
        .catch(error => console.error('Error checking updates:', error));    
}


setInterval(checkCommunication, 500);
setInterval(checkUpdates, 500);
