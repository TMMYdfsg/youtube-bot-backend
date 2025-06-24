# app.py (ログイン機能付き 完成版)

import os
import threading
import logging
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from functools import wraps # ★★★ 門番機能のためにインポート

from bot_runner import start_bot
from youtube.live_monitor import get_latest_logs
from youtube.chat import send_message
import shared_state
from database import init_db

app = Flask(__name__)
# .envファイルからSECRET_KEYを読み込む
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
CORS(app, supports_credentials=True) # ★★★ credentialsを許可

# --- ログインしているかチェックする「門番」機能 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function
# ---------------------------------------------

# --- 認証API ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # ユーザー名とパスワードは.envなどで管理するのが望ましい
    # 今回は簡単のため、ここに直接記述します
    USERNAME = "admin"
    PASSWORD = "ruka0927daisuki" # ★★★ 必ずあなただけのパスワードに変更してください

    if data.get('username') == USERNAME and data.get('password') == PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/check-auth')
def check_auth():
    is_logged_in = 'logged_in' in session
    return jsonify({'is_logged_in': is_logged_in})
# -----------------

@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "YouTube Bot Running"})

# --- ログインが必要なAPIに「門番」を設置 ---
@app.route("/api/status")
@login_required
def bot_status():
    is_live = shared_state.CURRENT_LIVE_CHAT_ID is not None
    video_id = shared_state.CURRENT_VIDEO_ID
    return jsonify({"bot_running": True, "is_live": is_live, "video_id": video_id})

@app.route("/api/chat-log")
@login_required
def chat_log():
    return jsonify(get_latest_logs())

@app.route('/api/send-message', methods=['POST'])
@login_required
def handle_send_message():
    # ... (この関数の内容は変更なし) ...
    data = request.get_json()
    message = data.get('message')
    if not message: return jsonify({'error': 'Message cannot be empty.'}), 400
    chat_id = shared_state.CURRENT_LIVE_CHAT_ID
    youtube = shared_state.YOUTUBE_SERVICE
    if not chat_id or not youtube: return jsonify({'error': 'Bot is not currently in a live chat session.'}), 404
    try:
        send_message(youtube, chat_id, message)
        return jsonify({'success': True, 'message': 'Message sent successfully.'})
    except Exception as e:
        logging.exception(f"Failed to send message via API: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500
# ---------------------------------------------

if __name__ == "__main__":
    init_db()
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
