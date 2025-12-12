import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from core.auth import is_logged_in, login_user, logout_user, get_current_user
from core.data import (
    load_users, save_users,
    add_user, edit_user, delete_user,
    toggle_active,
    load_logs, append_user_log, clear_logs
)
from core.telegram_client import (
    api_send_code, api_confirm_code, api_get_dialogs, api_send_message_loop
)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "devkey123")


# ------------------ Auth routes ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        if username in users and users[username]["password"] == password:
            login_user(username)
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Usuário ou senha incorretos.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# ------------------ Dashboard ------------------
@app.route("/")
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    user = get_current_user()
    user_id = session["user"]
    return render_template("dashboard.html", user=user, user_id=user_id)


# ------------------ Admin pages ------------------
@app.route("/admin")
def admin_page():
    if not is_logged_in():
        return redirect(url_for("login"))
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return "Acesso proibido", 403
    return render_template("admin.html")


@app.route("/admin/list")
def admin_list():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403
    return jsonify(load_users())


@app.route("/admin/create", methods=["POST"])
def admin_create():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403

    data = request.json or {}
    try:
        add_user(
            uid = data["uid"],
            password = data["password"],
            role = data.get("role","user"),
            active = bool(data.get("active", True)),
            phone = data.get("phone","")
        )
        append_user_log(user= user.get("role","admin"), entry={"action":"admin_create_user","target":data["uid"]})
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","error": str(e)}), 400


@app.route("/admin/edit", methods=["POST"])
def admin_edit():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403

    data = request.json or {}
    uid = data.get("uid")
    try:
        edit_user(
            old_uid = uid,
            password = data.get("password", None),
            active = data.get("active", None),
            phone = data.get("phone", None)
        )
        append_user_log(user= user.get("role","admin"), entry={"action":"admin_edit_user","target":uid})
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","error": str(e)}), 400


@app.route("/admin/delete", methods=["POST"])
def admin_delete():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403

    data = request.json or {}
    uid = data.get("uid")
    try:
        delete_user(uid)
        append_user_log(user= user.get("role","admin"), entry={"action":"admin_delete_user","target":uid})
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","error": str(e)}), 400


@app.route("/admin/toggle_active", methods=["POST"])
def admin_toggle_active():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403

    data = request.json or {}
    uid = data.get("uid")
    state = bool(data.get("state", False))
    try:
        toggle_active(uid, state)
        append_user_log(user= user.get("role","admin"), entry={"action":"admin_toggle_active","target":uid,"state":state})
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error","error": str(e)}), 400


@app.route("/admin/clear_logs", methods=["POST"])
def admin_clear_logs():
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403

    clear_logs()
    append_user_log(user= user.get("role","admin"), entry={"action":"admin_clear_logs"})
    return jsonify({"status":"ok"})


@app.route("/admin/logs/<uid>")
def admin_get_logs(uid):
    if not is_logged_in():
        return jsonify({"status":"error","error":"not logged"}), 401
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"status":"error","error":"forbidden"}), 403
    logs = load_logs()
    user_logs = [l for l in logs if l.get("uid")==uid]
    return jsonify(user_logs)


# ------------------ Telegram API ------------------
@app.route("/api/send_code", methods=["POST"])
def api_send_code_route():
    data = request.get_json() or {}
    phone = data.get("phone")
    res = api_send_code(phone)
    return jsonify(res)


@app.route("/api/confirm_code", methods=["POST"])
def api_confirm_code_route():
    data = request.get_json() or {}
    phone = data.get("phone")
    code = data.get("code")
    phone_hash = data.get("phone_hash")
    res = api_confirm_code(phone, code, phone_hash)
    return jsonify(res)


@app.route("/api/list_groups", methods=["POST"])
def api_list_groups_route():
    data = request.get_json() or {}
    phone = data.get("phone")
    res = api_get_dialogs(phone)
    return jsonify(res)


@app.route("/api/start_attack", methods=["POST"])
def api_start_attack_route():
    data = request.get_json() or {}
    phone = data.get("phone")
    chat_id = data.get("chat_id")
    message = data.get("message")
    res = api_send_message_loop(phone, chat_id, message)
    return jsonify(res)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
