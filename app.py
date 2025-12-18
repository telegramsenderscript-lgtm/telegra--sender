import os
from flask import Flask, request, jsonify

from core.telegram_client import (
    api_send_code,
    api_confirm_code
)

app = Flask(__name__)


@app.route("/api/send_code", methods=["POST"])
def send_code():
    data = request.get_json() or {}
    phone = data.get("phone")
    return jsonify(api_send_code(phone))


@app.route("/api/confirm_code", methods=["POST"])
def confirm_code():
    data = request.get_json() or {}
    phone = data.get("phone")
    code = data.get("code")
    return jsonify(api_confirm_code(phone, code))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
