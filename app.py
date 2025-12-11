import os
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


# ========================== LOGIN / LOGOUT ==============================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        # =================== DEBUG =====================
        app.logger.info("========== LOGIN DEBUG ==========")
        app.logger.info(f"Username recebido: {repr(username)}")
        app.logger.info(f"Password recebido: {repr(password)}")
        app.logger.info(f"Usuários carregados: {list(users.keys())}")

        if username not in users:
            app.logger.warning(f"Usuário não encontrado: {username}")
            return render_template("login.html", error="Usuário ou senha incorretos.")

        stored_pw = users[username].get("password")
        app.logger.info(f"Senha armazenada: {repr(stored_pw)}")

        if stored_pw != password:
            app.logger.warning(f"Senha incorreta para {username}")
            return render_template("login.html", error="Usuário ou senha incorretos.")

        # LOGIN OK
        app.logger.info(f"LOGIN OK — Usuário autenticado: {username}")
        login_user(username)
        return redirect(url_for("dashboard"))

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
    uid = session.get("user")

    return render_template("dashboard.html", user=user, user_id=uid)


# ========================== API TELEGRAM ==============================

@app.route("/send_code", methods=["POST"])
def send_code():
    user = get_current_user()
    return jsonify(api_send_code(user["phone"]))


@app.route("/confirm_code", methods=["POST"])
def confirm_code():
    data = request.get_json()
    code = data.get("code")
    phone_hash = data.get("phone_hash")

    user = get_current_user()
    return jsonify(api_confirm_code(user["phone"], code, phone_hash))


@app.route("/list_groups")
def list_groups():
    user = get_current_user()
    return jsonify(api_get_dialogs(user["phone"]))


@app.route("/start_attack", methods=["POST"])
def start_attack():
    data = request.get_json()
    msg = data.get("message")
    chat_id = data.get("chat_id")

    user = get_current_user()
    return jsonify(api_send_message_loop(user["phone"], chat_id, msg))


@app.route("/stop_attack", methods=["POST"])
def stop_attack():
    return jsonify({"status": "stopped"})


# ========================== RUN ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
