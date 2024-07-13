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
            location: navigator.location
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