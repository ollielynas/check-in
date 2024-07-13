

const d = new Date();
//let start_time = check_response(await get_press_info(getCookie("username")));
let start_time = d.getTime();
let session_end_time = start_time + 1000000000000;
let interval = 20;

function get_params_and_start_session() {
    const intervalp = Number.parseInt(document.getElementById("session-interval").innerText);
    const durationp = Number.parseInt(document.getElementById("session-duration").innerText);


    start_session(intervalp, durationp).then(res => {
        interval = intervalp;
        session_end_time = Date.now() + durationp * 60 * 1000;
        updateCheckinTime();
    });
}

function start_session_home() {
    document.body.setAttribute("in-session","true");
    const d = new Date();

    start_time = d.getTime();
    update_timer();
    updateCheckinTime();
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
    const d = new Date();
    let value =  d.getTime()- start_time;
    document.getElementById("timer").innerText  = msToTime(value);

    if (Date.now() >= session_end_time) {
        end_session_home();
        session_end_time = start_time + 1000000000000;
    }
}

setInterval(update_timer, 100); 

function end_session_home() {
    document.body.setAttribute("in-session","false");
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

windowOnLoad = async () => {
    if (getCookie("token") != null) {
        document.querySelector(".nav-sign-in-button").innerHTML = "<i class=\"ph ph-sign-out\"></i>";
        document.querySelector(".nav-sign-in-button").onclick = () => {
            document.cookie='token=;path=/;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
            window.location.reload();
        };
    }

    let resp = check_response(await get_press_info(getCookie("username")));

    if (resp !== "not in session") {
        start_session_home();

        start_time = Date.parse(resp["start"]);
        session_end_time = Date.parse(resp["stop"]);
        interval = resp["interval"];

        console.log(resp);
        if (resp["presses"].length != 0) {
            start_time = Date.parse(resp["presses"][resp["presses"].length - 1]["timestamp"]);
            console.log(resp["presses"][resp["presses"].length - 1]["timestamp"]);
        }

        update_timer();
        updateCheckinTime();
    }
}

function updateCheckinTime() {
    let time = start_time + interval * 60000;
    let time_str = new Date(time).toLocaleTimeString();
    let time_without_seconds = time_str.replace(/:\d{2}$/, '');

    document.getElementById("checkin-time").innerText = time_without_seconds;
}

async function checkIn() {
    const button = document.getElementById("checkin-button");
    button.innerText = "checking in .";

    let counter = 0;
    updateCallabck = () => {
        counter += 1;
        const amount = counter % 3 + 1;
        button.innerText = "checking in " + ".".repeat(amount);
    };

    const handle = setInterval(updateCallabck, 500);

    stopCallback = () => {
        clearInterval(handle);
        button.innerText = "checked in!";

        setTimeout(() => button.innerText = "check in", 5000);

        const d = new Date();
        start_time = d.getTime();
        update_timer();

        updateCheckinTime();
    }

    navigator.geolocation.getCurrentPosition(pos => {
        loc = pos.coords.latitude + ", " + pos.coords.longitude + ", " + pos.coords.accuracy;
        button_press(loc).then(stopCallback);
    }, err => {
        button_press().then(stopCallback);
    })
}



function OnlyNumber(e, allowedchars) {
    var key = e.charCode == undefined ? e.keyCode : e.charCode;
    if ((/^[0-9]+$/.test(String.fromCharCode(key))) || key == 0 || isPassKey(key, allowedchars)) { return true; }
    else { return false; }
}