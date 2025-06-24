# database.py

import sqlite3
import logging

DATABASE_FILE = "chat_history.db"

def init_db():
    """データベースとテーブルを初期化する"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # チャットログ用のテーブル（変更なし）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)
        
        # ★★★ ユーザー情報を保存するテーブルを追加 ★★★
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL
        )
        """)

        # ★★★ パスキー情報を保存するテーブルを追加 ★★★
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_credentials (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            public_key BLOB NOT NULL,
            sign_count INTEGER NOT NULL,
            transports TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        conn.commit()
        conn.close()
        logging.info(f"データベース '{DATABASE_FILE}' の初期化が完了しました。")
    
    except Exception as e:
        logging.error(f"データベースの初期化中にエラーが発生しました: {e}")

