import sqlite3
from flask import Flask, request, send_from_directory

conn = sqlite3.connect("db/db.sqlite")

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

setup_db()

app = Flask(__name__)

@app.route("/website/<path:path>", methods = ["GET"])
def serve_file(path):
    return send_from_directory('website', path)