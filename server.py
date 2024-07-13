import sqlite3, random
from flask import Flask, request, send_from_directory, redirect, render_template, Response, jsonify
from argon2 import PasswordHasher
import argon2
import json
import os
from datetime import datetime, timedelta
import pytz

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIMEZONE = pytz.timezone("Pacific/Auckland")

conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)

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

    conn.commit()

# setup_db()

app = Flask(__name__, template_folder="./website/")

@app.route("/")
def redirect_to_index():
    return redirect("/website/index.html")

@app.route("/website/register.html", methods = ["POST", "GET"])
def do_registration():
    if request.method == "GET":
        return render_template("register.html", errors = [])
    else:
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm-password"]
        remember = request.form["remember"] == "on" if "remember" in request.form else False

        if password != confirm:
            return render_template("register.html", errors = ["Passwords do not match!"])

        hasher = PasswordHasher()
        password_hash = hasher.hash(password)
        
        cur = conn.cursor()

        res = cur.execute("SELECT id, username FROM user WHERE username = ?", [username])
        if res.fetchone() is not None:
            return render_template("register.html", errors = ["Username is already in use!"])
        
        cur.execute("INSERT INTO user (username, password_hash) VALUES (?,?)", [username, password_hash])

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
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()


    if in_session:
        return Response(
            json.dumps({"error": "IN_SESSION"}),
            400,
            mimetype="application/json"
        )
    
    start_time = datetime.now(TIMEZONE).strftime(TIME_FORMAT)

    cur.execute("UPDATE user SET in_session = 1, session_start_time = ? WHERE id = ?", [start_time, user])

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

    username_res = cur.execute("SELECT id, in_session, session_start_time FROM user WHERE username = ?", [username]).fetchone()

    if username_res is None:
        res = Response(
            json.dumps({"error": "INVALID_USERNAME"}),
            400,
            mimetype="application/json"
        )

        return res

    (user_id, in_session, start_time) = username_res

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
            "presses": presses
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

    username_res = cur.execute("SELECT user.id, user.username, user.in_session, user.session_start_time FROM supervisor JOIN user ON user.id=supervisor.supervisee_id WHERE supervisor_id = ?", [user]).fetchall()

    res = {}

    for user_id, username, in_session, session_start in username_res:
        if not in_session:
            res[username] = "not in session"
        else:
            data = {}
            data["start"] = session_start

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


#LOCATION STUFF
# Store user locations in memory (for simplicity, use a database in production)
#user_locations = {}

# @app.route('/update_location', methods=['POST'])
# def update_location():
#     data = request.get_json()
#     user_id = "example_user"  # Replace with actual user ID from session/auth
#     user_locations[user_id] = (data['latitude'], data['longitude'])
#     return jsonify(success=True)

# @app.route('/get_location/<user_id>', methods=['GET'])
# def get_location(user_id):
#     location = user_locations.get(user_id)
#     if location:
#         return jsonify(latitude=location[0], longitude=location[1])
#     return jsonify(error="User not found"), 404

# if __name__ == '__main__':
#     app.run(debug=True)