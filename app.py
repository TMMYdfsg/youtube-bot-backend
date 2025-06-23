from flask import Flask, jsonify, request
from flask_cors import CORS
from bot_runner import start_bot
from youtube.live_monitor import get_latest_logs
import threading

app = Flask(__name__)
CORS(app)  # ✅ ReactからのCORS許可


@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "YouTube Bot Running"})


@app.route("/api/status")
def bot_status():
    # ライブ中かどうか判定（簡易）なども可
    return jsonify({"bot_running": True})


@app.route("/api/chat-log")
def chat_log():
    return jsonify(get_latest_logs())


@app.route("/api/test-gemini", methods=["POST"])
def test_gemini():
    from gemini.responder import generate_response

    data = request.get_json()
    prompt = data.get("message")
    result = generate_response(prompt)
    return jsonify({"response": result})


if __name__ == "__main__":
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
