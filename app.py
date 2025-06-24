# app.py (パスキー認証API付き 完成版)

import os
import threading
import logging
import base64
import sqlite3
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from functools import wraps
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential
from webauthn.helpers.cose import COSEAlgorithmIdentifier

from bot_runner import start_bot
from youtube.live_monitor import get_latest_logs
from youtube.chat import send_message
import shared_state
from database import init_db, DATABASE_FILE

# --- 初期設定 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')
CORS(app, supports_credentials=True)
RP_ID = "localhost"  # ★ デプロイ時はNetlifyのドメイン名に変更
RP_NAME = "Urausamaru Bot"
ORIGIN = "http://localhost:3000" # ★ デプロイ時はNetlifyのURLに変更

# --- ログインしているかチェックする「門番」機能 ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: # 'logged_in'から'user_id'に変更
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- 従来のID/パスワード認証API ---
# (省略... 必要なら残す)

# --- ★★★ パスキー認証API ★★★ ---
@app.route('/api/passkey/register-request', methods=['POST'])
def passkey_register_request():
    username = request.json.get('username')
    if not username: return jsonify({"error": "Username is required"}), 400

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user: return jsonify({"error": "Username already exists"}), 400

    user_id = os.urandom(16).hex()
    session['registration_user_id'] = user_id
    session['registration_username'] = username

    options = generate_registration_options(
        rp_id=RP_ID, rp_name=RP_NAME, user_id=user_id, user_name=username
    )
    session['challenge'] = options.challenge
    return jsonify(options.to_dict())

@app.route('/api/passkey/register-verify', methods=['POST'])
def passkey_register_verify():
    body = request.get_json()
    user_id = session.get('registration_user_id')
    username = session.get('registration_username')
    challenge = session.get('challenge')

    try:
        verification = verify_registration_response(
            credential=RegistrationCredential.parse_raw(body),
            expected_challenge=challenge.encode('utf-8'),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        cursor.execute(
            "INSERT INTO user_credentials (id, user_id, public_key, sign_count, transports) VALUES (?, ?, ?, ?, ?)",
            (verification.credential_id, user_id, verification.credential_public_key, verification.sign_count, ",".join(body.get('transports', [])))
        )
        conn.commit()
        conn.close()

        session.pop('registration_user_id', None)
        session.pop('registration_username', None)

        return jsonify({"verified": True})
    except Exception as e:
        return jsonify({"error": f"Verification failed: {e}"}), 400

@app.route('/api/passkey/login-request', methods=['POST'])
def passkey_login_request():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user_credentials")
    credentials = [{"id": row[0]} for row in cursor.fetchall()]
    conn.close()

    options = generate_authentication_options(rp_id=RP_ID, allow_credentials=credentials)
    session['challenge'] = options.challenge
    return jsonify(options.to_dict())

@app.route('/api/passkey/login-verify', methods=['POST'])
def passkey_login_verify():
    body = request.get_json()
    credential_id = body.get('id')
    challenge = session.get('challenge')

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, public_key, sign_count FROM user_credentials WHERE id = ?", (credential_id,))
    cred_info = cursor.fetchone()
    if not cred_info: return jsonify({"error": "Credential not found"}), 404
    
    user_id, public_key, sign_count = cred_info

    try:
        verification = verify_authentication_response(
            credential=AuthenticationCredential.parse_raw(body),
            expected_challenge=challenge.encode('utf-8'),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=public_key,
            credential_current_sign_count=sign_count,
        )
        
        cursor.execute("UPDATE user_credentials SET sign_count = ? WHERE id = ?", (verification.new_sign_count, credential_id))
        conn.commit()
        conn.close()

        session['user_id'] = user_id # ログイン状態をセッションに保存
        return jsonify({"verified": True})
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Verification failed: {e}"}), 400

# ... (他のAPIエンドポイントには @login_required を付ける) ...

if __name__ == "__main__":
    init_db()
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
