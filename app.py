import os
import threading
import time
import json
import asyncio
from flask import Flask, render_template, request, redirect, session, jsonify, send_file

from core.data import (
    load_users, save_users, add_user, edit_user, delete_user,
    append_user_log, load_user_logs, remove_session,
    now_iso, session_file
)

from core.telegram_client import (
    start_client_for_user,
    confirm_code_for_user,
    list_dialogs_for_user,
    send_message_for_user,
    logout_user_for_user
)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "troque_essa_chave")

# ------------------------------------------------------------------------
#  FIX DO TELETHON: event loop único em thread dedicada
# ------------------------------------------------------------------------

_bg_loop = asyncio.new_event_loop()

def _bg_loop_thread():
    asyncio.set_event_loop(_bg_loop)
    _bg_loop.run_forever()

_loop_thread = threading.Thread(target=_bg_loop_thread, daemon=True)
_loop_thread.start()

def run_async_in_thread(coro_func, *args, timeout: float = 30, **kwargs):
    """
    Executa corrotina no loop assíncrono permanente.
    Evita o erro 'event loop changed' do Telethon.
    """
    coro = coro_func(*args, **kwargs)
    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    try:
        return future.result(timeout=timeout)
    except Exception as e:
        try:
            future.cancel()
        except:
            pass
        return {"status": "error", "error": str(e)}

# ------------------------------------------------------------------------
# ATAQUES
# ------------------------------------------------------------------------

ATTACKS = {}


# ---------- Helpers ----------
def require_login(func):
    from functools import wraps
    @wraps(func)
    def wr(*a, **kw):
        if "user" not in session:
            return redirect("/login")
        return func(*a, **kw)
    return wr


# ---------- Routes ----------
@app.route("/")
def index():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        uid = request.form.get("username", "").strip()
        pwd = request.form.get("password", "")
        users = load_users()
        u = users.get(uid)
        if not u or u.get("password") != pwd:
            error = "Usuário ou senha inválidos"
        else:
            session["user"] = uid
            append_user_log(uid, {"action": "login", "ts": now_iso()})
            return redirect("/dashboard")
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    uid = session.pop("user", None)
    if uid:
        append_user_log(uid, {"action": "logout", "ts": now_iso()})
    return redirect("/login")


@app.route("/dashboard")
@require_login
def dashboard():
    uid = session["user"]
    users = load_users()
    u = users.get(uid, {})
    return render_template("dashboard.html", user_id=uid, user=u)


# ---------- Admin ----------
@app.route("/admin", methods=["GET", "POST"])
@require_login
def admin():
    uid = session["user"]
    users = load_users()
    cur = users.get(uid, {})
    if cur.get("role") != "admin":
        return "Acesso proibido", 403

    msg = ""
    if request.method == "POST" and request.form.get("action") == "create":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        phone = request.form.get("phone", "")
        active = 1 if request.form.get("active") == "on" else 0
        role = request.form.get("role", "user")
        try:
            add_user(username, password, role=role, active=bool(active), phone=phone)
            append_user_log(username, {
                "action": "created_by_admin",
                "ts": now_iso(),
                "by": uid
            })
            msg = "Usuário criado"
            users = load_users()
        except Exception as e:
            msg = str(e)

    return render_template("admin.html", users=users, message=msg, cur=cur)


@app.route("/admin/delete/<target>")
@require_login
def admin_delete(target):
    uid = session["user"]
    users = load_users()
    cur = users.get(uid, {})
    if cur.get("role") != "admin":
        return "forbidden", 403
    delete_user(target)
    append_user_log(target, {
        "action": "deleted_by_admin",
        "ts": now_iso(),
        "by": uid
    })
    return redirect("/admin")


# ---------- Telegram endpoints ----------
@app.route("/send_code", methods=["POST"])
@require_login
def send_code():
    uid = session["user"]
    users = load_users()
    user = users.get(uid)
    phone = user.get("phone")
    if not phone:
        return jsonify({"status": "error", "error": "Telefone não cadastrado"}), 400

    res = run_async_in_thread(start_client_for_user, uid, phone)
    return jsonify(res)


@app.route("/confirm_code", methods=["POST"])
@require_login
def confirm_code():
    uid = session["user"]
    data = request.json or {}
    code = data.get("code", "")
    phone = load_users().get(uid, {}).get("phone")
    phone_hash = data.get("phone_hash")

    res = run_async_in_thread(
        confirm_code_for_user,
        uid, phone, code, phone_hash,
        timeout=60
    )

    if res.get("status") == "authorized":
        append_user_log(uid, {"action": "telegram_authorized", "ts": now_iso()})

    return jsonify(res)


@app.route("/list_groups", methods=["GET"])
@require_login
def list_groups():
    uid = session["user"]
    res = run_async_in_thread(list_dialogs_for_user, uid)
    return jsonify(res)


# ---------- Attack ----------
@app.route("/start_attack", methods=["POST"])
@require_login
def start_attack():
    uid = session["user"]
    data = request.json or {}
    chat_id = data.get("chat_id")
    message = data.get("message")
    delay_ms = int(data.get("delay_ms", 30))

    if not chat_id or not message:
        return jsonify({"status": "error", "error": "chat_id and message required"}), 400

    if ATTACKS.get(uid):
        return jsonify({"status": "error", "error": "attack already running"}), 400

    stop_event = threading.Event()

    def attack_worker():
        while not stop_event.is_set():
            start_t = time.perf_counter()

            res = run_async_in_thread(
                send_message_for_user, uid, chat_id, message
            )

            if res.get("status") == "ok":
                ping = (time.perf_counter() - start_t) * 1000
                append_user_log(uid, {
                    "action": "sent_message",
                    "chat_id": chat_id,
                    "ping_ms": round(ping, 2),
                    "ts": now_iso()
                })
                break

            time.sleep(max(0.001, delay_ms / 1000))

        ATTACKS.pop(uid, None)

    t = threading.Thread(target=attack_worker, daemon=True)
    ATTACKS[uid] = {"thread": t, "stop_event": stop_event}
    t.start()

    return jsonify({"status": "attack_started"})


@app.route("/stop_attack", methods=["POST"])
@require_login
def stop_attack():
    uid = session["user"]
    info = ATTACKS.get(uid)
    if not info:
        return jsonify({"status": "error", "error": "no attack running"}), 400
    info["stop_event"].set()
    return jsonify({"status": "stopping"})


# ---------- Utils ----------
@app.route("/user/logs/<uid>")
@require_login
def get_user_logs(uid):
    logs = load_user_logs(uid)
    return jsonify(logs)


@app.route("/download/users.json")
@require_login
def download_users():
    path = os.path.join("assets", "users.json")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
