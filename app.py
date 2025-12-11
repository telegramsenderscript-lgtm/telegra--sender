import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from core.auth import is_logged_in, login_user, logout_user, get_current_user
from core.data import (
    load_users,
    add_user,
    edit_user,
    delete_user,
    toggle_active
)
from core.telegram_client import (
    api_send_code,
    api_confirm_code,
    api_get_dialogs,
    api_send_message_loop
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey123")


# ------------------------- LOGIN -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form.get("username")
        password = request.form.get("password")

        for uid, u in users.items():
            if uid == username and u["password"] == password:
                login_user(uid)
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Usuário ou senha incorretos.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# ------------------------- DASHBOARD -------------------------

@app.route("/")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    user_id = session["user"]
    user = get_current_user()

    return render_template("dashboard.html", user=user, user_id=user_id)


# ------------------------- ADMIN PAGES -------------------------

@app.route("/admin")
def admin_page():
    user = get_current_user()
    if not user or user["role"] != "admin":
        return redirect("/")

    return render_template("admin.html")


@app.route("/admin/list")
def admin_list():
    return jsonify(load_users())


@app.route("/admin/create", methods=["POST"])
def admin_create():
    data = request.json
    try:
        add_user(
            uid=data["uid"],
            password=data["password"],
            role="user",
            active=data["active"],
            phone=data["phone"]
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.route("/admin/edit", methods=["POST"])
def admin_edit():
    data = request.json
    try:
        edit_user(
            old_uid=data["uid"],
            password=data["password"],
            active=data["active"],
            phone=data["phone"]
        )
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    data = request.json
    try:
        delete_user(data["uid"])
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.route("/admin/toggle_active", methods=["POST"])
def admin_toggle_active():
    data = request.json
    try:
        toggle_active(data["uid"], data["state"])
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


# ---------------- TELEGRAM API ----------------

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
