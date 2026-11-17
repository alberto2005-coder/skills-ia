import os
import sqlite3
import subprocess


def get_user(request):
    user_id = request.args.get("id")
    connection = sqlite3.connect("app.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + user_id)
    return cursor.fetchone()


def run_report(request):
    target = request.args.get("target")
    return subprocess.run("nmap " + target, shell=True)


def render_comment(request):
    body = request.form.get("body")
    return "<div>" + body + "</div>"
