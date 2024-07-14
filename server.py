import sqlite3, random
from flask import Flask, request, send_from_directory, redirect, render_template, Response, jsonify
from argon2 import PasswordHasher
import argon2
import json
import os
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
import pytz
import yagmail

SENDER_EMAIL_ADDRESS = {"dummyemail8001@gmail.com": "Check-in Chicken"}
yag = yagmail.SMTP(SENDER_EMAIL_ADDRESS, oauth2_file='oauth_yagmail.json')

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMEZONE = pytz.timezone("Pacific/Auckland")

conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)

def send_email(yag, to, subject, contents):
    print("Sending email to", to, "with subject '" + subject + "'")
    print("=== EMAIL CONTENTS BEGIN ===")
    print(contents)
    print("=== EMAIL CONTENTS END ===")
    yag.send(to=to, subject=subject, contents=contents)

def setup_db():
    if not os.path.exists("./db"):
        os.mkdir("db")

    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS user")
    cur.execute("DROP TABLE IF EXISTS session")
    cur.execute("DROP TABLE IF EXISTS button_press")
    cur.execute("DROP TABLE IF EXISTS supervisor")

    cur.execute("""CREATE TABLE user(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                username STRING NOT NULL,
                password_hash STRING NOT NULL,

                in_session INTEGER NOT NULL DEFAULT 0,
                session_start_time STRING
    )""")

    cur.execute("""CREATE TABLE session(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                token STRING NOT NULL,
                user_id INTEGER NOT NULL,

                creation STRING NOT NULL,
                expiry STRING NOT NULL
    )""")
    
    cur.execute("""CREATE TABLE button_press(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                user_id INTEGER NOT NULL,

                timestamp STRING NOT NULL,
                location STRING
    )""")

    cur.execute("""CREATE TABLE supervisor(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,

                supervisor_id INTEGER NOT NULL,
                supervisee_id INTEGER NOT NULL
    )""")

    cur.execute("ALTER TABLE user ADD checkin_interval INTEGER")
    cur.execute("ALTER TABLE user ADD session_stop STRING")
    cur.execute("ALTER TABLE user ADD last_checkin STRING")
    cur.execute("ALTER TABLE user ADD alerted INTEGER NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE user ADD email STRING")

    conn.commit()

#setup_db()

app = Flask(__name__, template_folder="./website/")

@app.route("/")
def redirect_to_index():
    return redirect("/website/index.html")

@app.route("/favicon.ico")
def serve_favicon():
    return serve_file("favicon.ico")

@app.route("/website/register.html", methods = ["POST", "GET"])
def do_registration():
    if request.method == "GET":
        return render_template("register.html", errors = [])
    else:
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm-password"]
        email = request.form["email"]
        remember = request.form["remember"] == "on" if "remember" in request.form else False

        if password != confirm:
            return render_template("register.html", errors = ["Passwords do not match!"])

        hasher = PasswordHasher()
        password_hash = hasher.hash(password)
        
        cur = conn.cursor()

        res = cur.execute("SELECT id, username FROM user WHERE username = ?", [username])
        if res.fetchone() is not None:
            return render_template("register.html", errors = ["Username is already in use!"])
        
        cur.execute("INSERT INTO user (username, password_hash, email) VALUES (?,?,?)", [username, password_hash,email])

        conn.commit()

        return log_user_in(username, remember)
    
@app.route("/website/login.html", methods = ["POST", "GET"])
def do_login():
    if request.method == "GET":
        return render_template("login.html", errors = [])
    else:
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form["remember"] == "on" if "remember" in request.form else False

        cur = conn.cursor()
        res = cur.execute("SELECT password_hash FROM user WHERE username = ?", [username]).fetchone()

        if res is not None:
            (check_hash,) = res

            hasher = PasswordHasher()
            try:
                hasher.verify(check_hash, password)
            except argon2.exceptions.VerifyMismatchError:
                pass
            else:
                return log_user_in(username, remember)

        return render_template("login.html", errors = ["Username or password do not match!"])
    
@app.route("/api/start_session", methods = ["POST"])
def start_session():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    duration = int(request.args.get("duration"))
    interval = int(request.args.get("interval"))
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()

    if in_session:
        return Response(
            json.dumps({"error": "IN_SESSION"}),
            400,
            mimetype="application/json"
        )
    
    start_time = datetime.now(TIMEZONE).strftime(TIME_FORMAT)
    end_time = (datetime.now(TIMEZONE) + timedelta(minutes=duration)).strftime(TIME_FORMAT)

    cur.execute(
        "UPDATE user SET in_session = 1, session_start_time = ?, checkin_interval = ?, session_stop = ?, last_checkin = ?, alerted = 0 WHERE id = ?", 
        [start_time, interval, end_time, start_time, user]
    )

    conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

@app.route("/api/end_session", methods = ["POST"])
def end_session():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()

    if not in_session:
        return Response(
            json.dumps({"error": "NOT_IN_SESSION"}),
            400,
            mimetype="application/json"
        )
    
    start_time = datetime.now(TIMEZONE).strftime(TIME_FORMAT)

    cur.execute("UPDATE user SET in_session = 0 WHERE id = ?", [user])

    conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

@app.route("/api/button_press", methods = ["POST"])
def button_press():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()

    if not in_session:
        return Response(
            json.dumps({"error": "NOT_IN_SESSION"}),
            400,
            mimetype="application/json"
        )
    
    data = request.get_json(force=True)

    location = None
    if "location" in data:
        location = data["location"]
        assert type(location) == str

    timestamp = datetime.now(TIMEZONE).strftime(TIME_FORMAT)

    cur.execute("INSERT INTO button_press (user_id, timestamp, location) VALUES (?, ?, ?)", [user, timestamp, location])
    cur.execute("UPDATE user SET last_checkin = ?, alerted = 0 WHERE id = ?", [timestamp, user])

    conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

@app.route("/api/am_i_in_session", methods = ["GET"])
def is_in_session():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()

    return Response(json.dumps({"result": bool(in_session)}), 200, mimetype="application/json")

@app.route("/api/my_email", methods = ["GET"])
def get_my_email():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    cur = conn.cursor()
    (email,) = cur.execute("SELECT (email) FROM user WHERE id = ?", [user]).fetchone()

    return Response(json.dumps({"result": email}), 200, mimetype="application/json")

@app.route("/api/set_email", methods = ["POST"])
def set_my_email():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    email = request.args["email"]
    
    cur = conn.cursor()
    cur.execute("UPDATE user SET email = ? WHERE id = ?", [email, user])
    conn.commit()

    return Response(json.dumps({"result": email}), 200, mimetype="application/json")

@app.route("/api/add_supervisor", methods = ["POST"])
def add_supervisor():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    username = request.args.get('username')
    supervisor_id = get_id_from_username(username)

    if supervisor_id is None:
        res = Response(
            json.dumps({"error": "INVALID_USERNAME"}),
            400,
            mimetype="application/json"
        )

        return res
        
    if supervisor_id == user:
        res = Response(
            json.dumps({"error": "SELF_REFERENCE"}),
            400,
            mimetype="application/json"
        )

        return res

    cur = conn.cursor()
    if cur.execute("SELECT id FROM supervisor WHERE supervisee_id = ? AND supervisor_id = ?", [user, supervisor_id]).fetchone() is None:
        cur.execute("INSERT INTO supervisor (supervisor_id, supervisee_id) VALUES (?, ?)", [supervisor_id, user])
        conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

@app.route("/api/remove_supervisor", methods = ["POST"])
def remove_supervisor():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    username = request.args.get('username')
    supervisor_id = get_id_from_username(username)

    if supervisor_id is None:
        res = Response(
            json.dumps({"error": "INVALID_USERNAME"}),
            400,
            mimetype="application/json"
        )

        return res
        
    if supervisor_id == user:
        res = Response(
            json.dumps({"error": "SELF_REFERENCE"}),
            400,
            mimetype="application/json"
        )

        return res

    cur = conn.cursor()
    cur.execute("DELETE FROM supervisor WHERE supervisee_id = ? AND supervisor_id = ?", [user, supervisor_id])
    conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

@app.route("/api/supervisors", methods = ["GET"])
def get_supervisors():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res

    cur = conn.cursor()
    res = cur.execute("SELECT user.username FROM supervisor JOIN user ON user.id=supervisor.supervisor_id WHERE supervisee_id = ?", [user]).fetchall()
    res = [x[0] for x in res]

    return Response(json.dumps({"result": res}), 200, mimetype="application/json")

@app.route("/api/supervisees", methods = ["GET"])
def get_supervisees():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res

    cur = conn.cursor()
    res = cur.execute("SELECT user.username FROM supervisor JOIN user ON user.id=supervisor.supervisee_id WHERE supervisor_id = ?", [user]).fetchall()
    res = [x[0] for x in res]

    return Response(json.dumps({"result": res}), 200, mimetype="application/json")

@app.route("/api/presses", methods = ["GET"])
def get_presses():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res
    
    username = request.args.get('username')

    cur = conn.cursor()

    username_res = cur.execute("SELECT id, in_session, session_start_time, session_stop, checkin_interval, alerted FROM user WHERE username = ?", [username]).fetchone()

    if username_res is None:
        res = Response(
            json.dumps({"error": "INVALID_USERNAME"}),
            400,
            mimetype="application/json"
        )

        return res

    (user_id, in_session, start_time, stop_time, checkin_interval, alerted) = username_res

    allowed = True
    if user_id != user:
        allowed = cur.execute("SELECT supervisor_id FROM supervisor WHERE supervisor_id = ? AND supervisee_id = ?", [user, user_id]).fetchone() is not None

    if not allowed:
        res = Response(
            json.dumps({"error": "FORBIDDEN"}),
            400,
            mimetype="application/json"
        )

        return res

    if not in_session:
        res = "not in session"
    else:
        presses = cur.execute("SELECT timestamp, location FROM button_press WHERE user_id = ? AND timestamp >= ?", [user_id, start_time]).fetchall()

        presses = [
            {
                "timestamp": timestamp,
                "location": location
            }
            for (timestamp, location) in presses
        ]

        res = {
            "start": start_time,
            "stop": stop_time,
            "interval": checkin_interval,
            "presses": presses,
            "alerted": alerted
        }

    return Response(json.dumps({"result": res}), 200, mimetype="application/json")

@app.route("/api/all_presses", methods = ["GET"])
def get_all_presses():
    user = authenticate_user()

    if user is None:
        res = Response(
            json.dumps({"error": "NOT_LOGGED_IN"}),
            403,
            mimetype="application/json"
        )

        res.set_cookie("token", "", expires=0)

        return res

    cur = conn.cursor()

    username_res = cur.execute("SELECT user.id, user.username, user.in_session, user.session_start_time, user.session_stop, user.checkin_interval, user.last_checkin FROM supervisor JOIN user ON user.id=supervisor.supervisee_id WHERE supervisor_id = ?", [user]).fetchall()

    res = {}

    for user_id, username, in_session, session_start, session_stop, interval, last_checkin in username_res:
        if not in_session:
            res[username] = "not in session"
        else:
            data = {}
            data["start"] = session_start
            data["interval"] = interval
            data["stop"] = session_stop
            data["last_checkin"] = last_checkin

            presses = cur.execute("SELECT timestamp, location FROM button_press WHERE user_id = ? AND timestamp >= ?", [user_id, session_start]).fetchall()
            presses = [
                {
                    "timestamp": timestamp,
                    "location": location
                }
                for (timestamp, location) in presses
            ]

            data["presses"] = presses

            res[username] = data

    return Response(json.dumps({"result": res}), 200, mimetype="application/json")

@app.route("/website/<path:path>")
def serve_file(path):
    return send_from_directory('website', path)
    
def log_user_in(username, extend):
    cur = conn.cursor()

    res = cur.execute("SELECT id FROM user WHERE username = ?", [username])
    user_id = res.fetchone()[0]
    print(user_id)

    num_seconds = (86400 if extend else 3600)

    token = "".join(random.choice("abcdefghijklmnopqrstuvwxyzACDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(100))

    creation_time = datetime.now(TIMEZONE)
    expiry_time = creation_time + timedelta(seconds=num_seconds)

    cur.execute("INSERT INTO session (token, user_id, creation, expiry) VALUES (?, ?, ?, ?)", [
        token, 
        user_id,
        creation_time.strftime(TIME_FORMAT),
        expiry_time.strftime(TIME_FORMAT)
    ])

    conn.commit()

    response = redirect("/website/index.html")
    response.set_cookie("token", token, max_age=num_seconds)
    response.set_cookie("username", username, max_age=num_seconds)

    return response

def authenticate_user():
    if "token" not in request.cookies:
        return None
    
    token = request.cookies["token"]
    cur = conn.cursor()

    res = cur.execute("SELECT user_id, expiry FROM session WHERE token = ?", [token])
    res = res.fetchone()
    if res is not None:
        (user_id, expiry_time) = res

        if expiry_time <= datetime.now(TIMEZONE).strftime(TIME_FORMAT):
            return None
        else:
            return user_id
    else:
        return None
    
def get_id_from_username(username):
    cur = conn.cursor()

    res = cur.execute("SELECT id FROM user WHERE username = ?", [username]).fetchone()

    if res is None: return None
    return res[0]

ALERT_EMAIL_SUBJECT = "Check-in Chicken Alert"
ALERT_EMAIL_CONTENTS = """
Your friend, {name} has not checked-in on Check-in Chicken. Give 'em a ring.

Best Regards,

Charlie
"""

def check(text):
    cur = conn.cursor()

    # Stop finished session
    now = datetime.now(TIMEZONE).strftime(TIME_FORMAT)
    #finished_sessions = cur.execute("SELECT id, username FROM user WHERE session_stop <= ?", [now]).fetchall()
    #print(finished_sessions)
    cur.execute("UPDATE user SET in_session = 0 WHERE session_stop <= ? AND in_session = 1 AND alerted = 0", [now])

    conn.commit()

    res = cur.execute("SELECT id, username, session_start_time, checkin_interval, last_checkin FROM user WHERE alerted = 0 AND in_session = 1").fetchall()
    
    for user_id, username, session_start, interval, last_checkin in res:
        alert_time = datetime.strptime(last_checkin + "+12:00", TIME_FORMAT + "%z") + timedelta(minutes=interval+5)
        print(username, alert_time)
        if alert_time <= datetime.now(TIMEZONE):
            print("Alerting")
            for email in cur.execute("SELECT user.email FROM supervisor JOIN user ON user.id=supervisor.supervisor_id WHERE supervisee_id = ?", [user_id]).fetchall():
                if email is not None and email != "":
                    try:
                        send_email(yag, email, ALERT_EMAIL_SUBJECT, ALERT_EMAIL_CONTENTS.format(name=username))
                    except:
                        pass
            
            cur.execute("UPDATE user SET alerted = 1 WHERE id = ?", [user_id])

    conn.commit()

scheduler = APScheduler()
scheduler.add_job(func=check, args=['job run'], trigger='interval', id='job', seconds=5)
scheduler.start()

#send_email(yag, "anatol.coen@gmail.com", "Test", "Test")
