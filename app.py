from flask import Flask, request, jsonify, render_template
from core.telegram_client import api_send_code, api_confirm_code

app = Flask(__name__)

# -------- UI --------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        phone = request.form.get("phone")
        res = api_send_code(phone)
        if res["status"] != "ok":
            error = res.get("error")
        else:
            return render_template("confirm.html", phone=phone)
    return render_template("login.html", error=error)

@app.route("/confirm", methods=["POST"])
def confirm():
    phone = request.form.get("phone")
    code = request.form.get("code")
    return jsonify(api_confirm_code(phone, code))

# -------- API --------
@app.route("/api/send_code", methods=["POST"])
def api_send():
    phone = request.json.get("phone")
    return jsonify(api_send_code(phone))

@app.route("/api/confirm_code", methods=["POST"])
def api_confirm():
    phone = request.json.get("phone")
    code = request.json.get("code")
    return jsonify(api_confirm_code(phone, code))

if __name__ == "__main__":
    app.run(debug=True)
