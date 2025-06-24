# app.py

import threading
import logging # loggingをインポート（エラー記録のため）
from flask import Flask, jsonify, request
from flask_cors import CORS

from bot_runner import start_bot
from youtube.live_monitor import get_latest_logs
from youtube.chat import send_message
import shared_state
from database import init_db

app = Flask(__name__)
CORS(app)

@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "YouTube Bot Running"})

@app.route("/api/status")
def bot_status():
    # ライブ中かどうかに応じて、より詳細なステータスを返すことも可能
    is_live = shared_state.CURRENT_LIVE_CHAT_ID is not None
    return jsonify({"bot_running": True, "is_live": is_live})

@app.route("/api/chat-log")
def chat_log():
    return jsonify(get_latest_logs())

# test-geminiのエンドポイントは今回は省略（必要なら残してください）

@app.route('/api/send-message', methods=['POST'])
def handle_send_message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message key is missing or data is not a valid JSON.'}), 400

    message = data.get('message')

    if not message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    chat_id = shared_state.CURRENT_LIVE_CHAT_ID
    youtube = shared_state.YOUTUBE_SERVICE

    if not chat_id or not youtube:
        return jsonify({'error': 'Bot is not currently in a live chat session.'}), 404

    try:
        send_message(youtube, chat_id, message)
        return jsonify({'success': True, 'message': 'Message sent successfully.'})
    except Exception as e:
        # エラー内容をサーバーのログにも記録する
        logging.exception(f"Failed to send message via API: {e}")
        return jsonify({'error': 'An internal error occurred while sending the message.'}), 500

if __name__ == "__main__":
    init_db()  # ★★★ 2. アプリケーション起動時にDBを初期化 ★★★

    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
