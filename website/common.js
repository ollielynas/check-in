async function start_session(interval, duration) {
    await fetch(`/api/start_session?interval=${interval}&duration=${duration}`, {
        method: "POST"
    });
}


function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

function doSomething() {
    var myCookie = getCookie("MyCookie");

    if (myCookie == null) {
        // do cookie doesn't exist stuff;
    }
    else {
        // do cookie exists stuff
    }
}

function end_session() {
    fetch("/api/end_session", {
        method: "POST"
    });
}

window.onload = () => {
    if (getCookie("token") != null) {
        document.querySelector(".sign-in-button").innerHTML = "<i class=\"ph ph-sign-out\"></i>";
    }
}

async function button_press(location) {
    data = {}

    if (location) {
        data.location = location;
    }

    return await fetch("/api/button_press", {
        body: JSON.stringify(data),
        method: "POST"
    })
}

async function add_supervisor(username) {
    return await fetch(`/api/add_supervisor?username=${encodeURIComponent(username)}`, {
        "method": "POST"
    })
}

async function remove_supervisor(username) {
    return await fetch(`/api/remove_supervisor?username=${encodeURIComponent(username)}`, {
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
    return (await (await fetch(`/api/all_presses`, {cache: "no-store"})).json());
}