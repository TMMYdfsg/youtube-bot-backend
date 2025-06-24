# database.py

import sqlite3
import logging

DATABASE_FILE = "chat_history.db"


def init_db():
    """
    データベースとテーブルを初期化（存在しない場合のみ作成）する関数
    """
    try:
        # データベースに接続（ファイルがなければ自動的に作成される）
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # chat_logs テーブルを作成
        # IF NOT EXISTS をつけることで、すでにテーブルが存在する場合は何もしない
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
        )

        conn.commit()
        conn.close()
        logging.info(f"データベース '{DATABASE_FILE}' の初期化が完了しました。")

    except Exception as e:
        logging.error(f"データベースの初期化中にエラーが発生しました: {e}")
