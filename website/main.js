function start_session() {
    document.body.setAttribute("in-session","true");
    fetch("/api/start_session", {
        method: "POST"
    });
}
function end_session() {
    document.body.setAttribute("in-session","false");
    
    fetch("/api/end_session", {
        method: "POST"
    });
}


function button_press() {
    fetch("/api/button_press", {
        body: JSON.stringify({
            /* Put location here, "location": "Some location in a string format" */
            location: navigator.location
        }),
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

function getCookie(name) {
    var dc = document.cookie;
    var prefix = name + "=";
    var begin = dc.indexOf("; " + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) return null;
    }
    else
    {
        begin += 2;
        var end = document.cookie.indexOf(";", begin);
        if (end == -1) {
        end = dc.length;
        }
    }
    // because unescape has been deprecated, replaced with decodeURI
    //return unescape(dc.substring(begin + prefix.length, end));
    return decodeURI(dc.substring(begin + prefix.length, end));
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

window.onload = () => {
    if (getCookie("token") != null) {
        document.querySelector(".sign-in-button").innerHTML = "<i class=\"ph ph-sign-out\"></i>";
    }
}