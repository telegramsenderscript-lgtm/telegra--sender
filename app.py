from flask import Flask, request, jsonify, render_template
from core.telegram_client import api_send_code, api_confirm_code

app = Flask(__name__)

# =========================
# UI (HTML)
# =========================

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()

        if not phone:
            error = "Telefone obrigatório"
        else:
            res = api_send_code(phone)
            if res.get("status") != "ok":
                error = res.get("error", "Erro ao enviar código")
            else:
                return render_template("confirm.html", phone=phone)

    return render_template("login.html", error=error)


@app.route("/confirm", methods=["POST"])
def confirm():
    phone = request.form.get("phone", "").strip()
    code = request.form.get("code", "").strip()

    if not phone or not code:
        return jsonify({"status": "error", "error": "phone or code missing"})

    return jsonify(api_confirm_code(phone, code))


# =========================
# API (JSON)
# =========================

@app.route("/api/send_code", methods=["POST"])
def api_send():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()

    if not phone:
        return jsonify({"status": "error", "error": "phone missing"})

    return jsonify(api_send_code(phone))


@app.route("/api/confirm_code", methods=["POST"])
def api_confirm():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()
    code = data.get("code", "").strip()

    if not phone or not code:
        return jsonify({"status": "error", "error": "phone or code missing"})

    return jsonify(api_confirm_code(phone, code))


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)
