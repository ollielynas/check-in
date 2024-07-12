import sqlite3, random
from flask import Flask, request, send_from_directory, redirect, render_template, Response
from argon2 import PasswordHasher
import argon2
import json
from datetime import datetime, timedelta

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)

def setup_db():
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS user")
    cur.execute("DROP TABLE IF EXISTS session")

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

    conn.commit()

setup_db()

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
        return Response(
            json.dumps({"error": "unauthenticated"}),
            403,
            mimetype="application/json"
        )
    
    cur = conn.cursor()
    (in_session,) = cur.execute("SELECT (in_session) FROM user WHERE id = ?", [user]).fetchone()


    if in_session:
        return Response(
            json.dumps({"error": "session already started"}),
            400,
            mimetype="application/json"
        )
    
    start_time = datetime.now().strftime(TIME_FORMAT)

    cur.execute("UPDATE user SET in_session = 1, session_start_time = ? WHERE id = ?", [start_time, user])

    conn.commit()

    return Response(json.dumps({"result": "success"}), 200, mimetype="application/json")

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

    creation_time = datetime.now()
    expiry_time = creation_time + timedelta(seconds=num_seconds)

    cur.execute("INSERT INTO session (token, user_id, creation, expiry) VALUES (?, ?, ?, ?)", [
        token, 
        user_id,
        creation_time.strftime(TIME_FORMAT),
        expiry_time.strftime(TIME_FORMAT)
    ])

    conn.commit()

    response = redirect("/website/index.html")
    response.set_cookie("token", token, max_age=num_seconds, httponly=True)

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

        if expiry_time <= datetime.now().strftime(TIME_FORMAT):
            return None
        else:
            return user_id
    else:
        return None