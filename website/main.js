

const d = new Date();
let start_time = d.getTime();

function start_session() {
    start_time = d.getTime();
    document.body.setAttribute("in-session","true");
    fetch("/api/start_session", {
        method: "POST"
    });
}

function msToTime(duration) {
    var milliseconds = duration,
      seconds = Math.floor((duration / 1000) % 60),
      minutes = Math.floor((duration / (1000 * 60)) % 60),
      hours = Math.floor((duration / (1000 * 60 * 60)) % 24);
  
    hours = (hours < 10) ? "0" + hours : hours;
    minutes = (minutes < 10) ? "0" + minutes : minutes;
    seconds = (seconds < 10) ? "0" + seconds : seconds;
  
    return hours + ":" + minutes + ":" + seconds;
  }

function update_timer() {
    let value =  d.getTime()- start_time;
    console.log(value);
    document.getElementById("timer").innerText  = msToTime(value);
}

setInterval(update_timer, 1000); 

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

async function checkIn() {
    navigator.geolocation.getCurrentPosition(pos => {
        loc = pos.coords.latitude + ", " + pos.coords.longitude + ", " + pos.coords.accuracy;
        button_press(loc);
    }, err => {
        button_press();
    })
}