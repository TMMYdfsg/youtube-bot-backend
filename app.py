# app.py (ログイン機能なし・シンプル版)

import os
import threading
import logging
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

from bot_runner import start_bot
from youtube.live_monitor import get_latest_logs
from youtube.chat import send_message
import shared_state
from database import init_db, DATABASE_FILE

# --- 初期設定 ---
app = Flask(__name__)
# ★★★ どんなURLからのアクセスも許可するシンプルなCORS設定に戻します ★★★
CORS(app)

# --- APIエンドポイント ---
# ログイン機能が不要になったため、@login_required デコレーターはすべて削除します

@app.route("/")
def health_check():
    return jsonify({"status": "ok", "message": "YouTube Bot Running"})

@app.route("/api/status")
def bot_status():
    is_live = shared_state.CURRENT_LIVE_CHAT_ID is not None
    video_id = shared_state.CURRENT_VIDEO_ID
    return jsonify({"bot_running": True, "is_live": is_live, "video_id": video_id})

@app.route("/api/chat-log")
def chat_log():
    return jsonify(get_latest_logs())

@app.route('/api/send-message', methods=['POST'])
def handle_send_message():
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

# ★★★★★ ここから分析用APIを新しく追加 ★★★★★
@app.route('/api/analyze-user', methods=['POST'])
def handle_analyze_user():
    data = request.get_json()
    author_name = data.get('author')
    if not author_name:
        return jsonify({'error': 'Author name is required'}), 400

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # 'user'タイプのログから、指定された発言者のコメントのみを最大100件取得
        cursor.execute(
            "SELECT message FROM chat_logs WHERE log_type = 'user' AND author = ? ORDER BY timestamp DESC LIMIT 100",
            (author_name,)
        )
        comments = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not comments:
            return jsonify({'analysis': f'"{author_name}"さんのコメントは見つかりませんでした。'})

        # 取得したコメントをAIに渡して分析させる
        analysis_result = analyze_user_comments(comments)
        
        return jsonify({'analysis': analysis_result})

    except Exception as e:
        logging.error(f"ユーザー分析中にエラー: {e}")
        return jsonify({'error': 'An internal error occurred during analysis.'}), 500
# ★★★★★ ここまで追加 ★★★★★


if __name__ == "__main__":
    init_db()
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=False)
