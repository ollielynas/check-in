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

function button_press(location) {
    data = {}

    if (location) {
        data.location = location;
    }

    fetch("/api/button_press", {
        body: JSON.stringify(data),
        method: "POST"
    })
}

async function add_supervisor(username) {
    await fetch(`/api/add_supervisor?username=${encodeURIComponent(username)}`, {
        "method": "POST"
    })
}

async function remove_supervisor(username) {
    await fetch(`/api/remove_supervisor?username=${encodeURIComponent(username)}`, {
        "method": "POST"
    })
}

function check_response(res) {
    if ("error" in res) {
        if (res["error"] == "NOT_LOGGED_IN") {
            window.location = "/website/login.html";
        }
    }

    return res["result"]
}

async function am_i_in_session() {
    return (await (await fetch("/api/am_i_in_session")).json());
}

async function get_supervisors() {
    return (await (await fetch("/api/supervisors")).json());
}

async function get_supervisees() {
    return (await (await fetch("/api/supervisees")).json());
}

async function get_press_info(username) {
    return (await (await fetch(`/api/presses?username=${encodeURIComponent(username)}`)).json());
}

async function get_all_presses() {
    return (await (await fetch(`/api/all_presses`)).json());
}