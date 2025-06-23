from youtube.live_monitor import monitor_live_stream
import logging


def start_bot():
    logging.basicConfig(
        filename="logs/bot.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    while True:
        try:
            monitor_live_stream()
        except Exception as e:
            logging.exception(f"Bot実行中にエラー発生: {e}")
