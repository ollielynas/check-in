import sqlite3
from flask import Flask, request, send_from_directory, redirect
from argon2 import PasswordHasher

conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)

def setup_db():
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS user")
    cur.execute("DROP TABLE IF EXISTS session")

    cur.execute("""CREATE TABLE user(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                username STRING NOT NULL,
                password_hash STRING NOT NULL
    )""")

    cur.execute("""CREATE TABLE session(
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                token STRING NOT NULL,
                user_id INTEGER NOT NULL
    )""")

    conn.commit()

#setup_db()

app = Flask(__name__)

@app.route("/website/<path:path>")
def serve_file(path):
    return send_from_directory('website', path)

@app.route("/")
def redirect_to_index():
    return redirect("/website/index.html")

@app.route("/api/login", methods = ["POST"])
def do_login():
    print(request.form)
    username = request.form["username"]
    password = request.form["password"]
    remeber = request.form["remember"] == "on"

@app.route("/api/register", methods = ["POST"])
def do_registration():
    username = request.form["username"]
    password = request.form["password"]

    hasher = PasswordHasher()
    password_hash = hasher.hash(password)
    
    cur = conn.cursor()

    res = cur.execute("SELECT id, username FROM user WHERE username = ?", [username])
    if True or res.fethcone() is not None:
        pass