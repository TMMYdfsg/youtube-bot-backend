# database.py

import sqlite3
import logging

# 使用するSQLiteファイル名
DATABASE_FILE = "chat_history.db"

# ----------------------------------------
# コメント取得機能（Gemini分析などで使用）
# ----------------------------------------
def get_recent_comments_by_user(username: str, limit: int = 20) -> list[str]:
    """
    指定したユーザー名のコメントを、最新順に最大limit件まで取得する。
    Geminiによる傾向分析などに使用される。
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT message FROM chat_logs
            WHERE author = ?
              AND log_type = 'user'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (username, limit)
        )

        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    
    except Exception as e:
        logging.error(f"ユーザーコメントの取得中にエラー: {e}")
        return []

# ----------------------------------------
# DB初期化（テーブル作成）
# ----------------------------------------
def init_db():
    """
    データベースと3つの主要テーブルを初期化する関数。
    - chat_logs: チャットのログ保存（Bot / ユーザー / System）
    - users: 登録ユーザー情報（WebAuthn連携用）
    - user_credentials: パスキーなどのセキュリティ情報
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # 1. チャットログ用のテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,       -- 'user' or 'bot' or 'system'
                author TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL       -- ISO形式で保存
            )
        """)

        # 2. 登録ユーザー情報
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,           -- UUIDなどを想定
                username TEXT UNIQUE NOT NULL  -- 表示名（チャット名）
            )
        """)

        # 3. パスキー・WebAuthn用の認証情報
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                id TEXT PRIMARY KEY,            -- Credential ID
                user_id TEXT NOT NULL,          -- users.id への外部キー
                public_key BLOB NOT NULL,
                sign_count INTEGER NOT NULL,
                transports TEXT,                -- JSON配列で保存
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        conn.commit()
        conn.close()
        logging.info(f"データベース '{DATABASE_FILE}' の初期化が完了しました。")
    
    except Exception as e:
        logging.error(f"データベースの初期化中にエラーが発生しました: {e}")
