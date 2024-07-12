function start_session() {
    document.body.setAttribute("in-session","true");
    fetch("/api/start_session", {
        method: "POST"
    });
}

function end_session() {
    fetch("/api/end_session", {
        method: "POST"
    });
}

function button_press() {
    fetch("/api/button_press", {
        body: JSON.stringify({
            /* Put location here, "location": "Some location in a string format" */
        }),
        method: "POST"
    })
}

function add_supervisor(username) {
    fetch(`/api/add_supervisor?username=${encodeURIComponent(username)}`, {
        "method": "POST"
    })
}

function remove_supervisor(username) {
    fetch(`/api/remove_supervisor?username=${encodeURIComponent(username)}`, {
        "method": "POST"
    })
}

async function am_i_in_session() {
    return (await (await fetch("/api/am_i_in_session")).json())["result"];
}

async function get_supervisors() {
    return (await (await fetch("/api/supervisors")).json())["result"];
}

async function get_supervisees() {
    return (await (await fetch("/api/supervisees")).json())["result"];
}

async function get_press_info(username) {
    return (await (await fetch(`/api/presses?username=${encodeURIComponent(username)}`)).json())["result"];
}