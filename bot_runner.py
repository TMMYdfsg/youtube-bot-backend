# bot_runner.py

# 必要なモジュールを追加
import time
import logging
from youtube.live_monitor import monitor_live_stream

def start_bot():
    # ログ設定: ファイルにエラーを記録できるようにする
    # これにより、後から「なぜBotが止まったか」を調査できます
    logging.basicConfig(
        filename='logs/bot.log', 
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        encoding='utf-8' # 文字化け対策
    )
    
    # 無限ループでBotの生存を監視する
    while True:
        try:
            # メインの監視ロジックを実行
            logging.info("Botの監視を開始します...")
            monitor_live_stream()
            # monitor_live_streamが正常に終了した場合（ライブ終了時など）
            logging.info("監視が一旦終了しました。60秒後に再開します。")
            time.sleep(60)

        except Exception as e:
            # monitor_live_streamで予期せぬエラーが発生した場合
            # エラー内容をログファイルに記録
            logging.exception(f"Bot実行中に致命的なエラーが発生: {e}")
            # 少し待ってからループを再開し、Botの復活を試みる
            logging.info("エラーのため、60秒後にBotの再起動を試みます...")
            time.sleep(60)

