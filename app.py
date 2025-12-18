from flask import Flask, request, jsonify, render_template
from core.telegram_client import api_send_code, api_confirm_code

app = Flask(__name__)

# =========================
# UI
# =========================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        res = api_send_code(phone)

        if res.get("status") == "ok":
            return render_template("confirm.html", phone=phone)

        return render_template("login.html")

    return render_template("login.html")


@app.route("/confirm", methods=["POST"])
def confirm():
    phone = request.form.get("phone")
    code = request.form.get("code")
    return jsonify(api_confirm_code(phone, code))


# =========================
# API
# =========================

@app.route("/api/send_code", methods=["POST"])
def api_send():
    data = request.json or {}
    return jsonify(api_send_code(data.get("phone")))


@app.route("/api/confirm_code", methods=["POST"])
def api_confirm():
    data = request.json or {}
    return jsonify(api_confirm_code(
        data.get("phone"),
        data.get("code")
    ))


if __name__ == "__main__":
    app.run(debug=True)
