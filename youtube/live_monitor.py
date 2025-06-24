# youtube/live_monitor.py (全機能統合 最終版)

import random
import time
import datetime
import logging
import sqlite3
from youtube.auth import get_authenticated_service
from youtube.chat import get_live_chat_id, poll_chat_messages, send_message
import shared_state
from config import TARGET_CHANNEL_ID
from gemini.responder import generate_response
from database import DATABASE_FILE


def is_live_ended(youtube, video_id: str) -> bool:
    try:
        video_details = (
            youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
        )
        if not video_details.get("items"):
            return True
        details = video_details["items"][0]["liveStreamingDetails"]
        return details.get("actualEndTime") is not None
    except Exception as e:
        logging.warning(f"終了チェック中にエラー: {e}")
        return False


chat_log_cache = []


def append_log(log_type: str, author: str, text: str):
    log_entry_for_cache = {
        "type": log_type,
        "author": author,
        "message": text,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    chat_log_cache.append(log_entry_for_cache)
    if len(chat_log_cache) > 50:
        chat_log_cache.pop(0)

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_logs (log_type, author, message, timestamp) VALUES (?, ?, ?, ?)",
            (log_type, author, text, log_entry_for_cache["timestamp"]),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"データベースへのログ書き込み中にエラー: {e}")


def get_latest_logs():
    return chat_log_cache


def monitor_live_stream():
    youtube = get_authenticated_service()
    shared_state.YOUTUBE_SERVICE = youtube
    live_chat_id, video_id = get_live_chat_id(youtube, TARGET_CHANNEL_ID)
    if not live_chat_id:
        logging.info("ライブ配信なし。リトライします...")
        shared_state.CURRENT_LIVE_CHAT_ID = None
        shared_state.CURRENT_VIDEO_ID = None
        time.sleep(30)
        return
    shared_state.CURRENT_LIVE_CHAT_ID = live_chat_id
    shared_state.CURRENT_VIDEO_ID = video_id
    logging.info(f"ライブ検出: VideoID={video_id}")
    ANNOUNCEMENT_MESSAGES = [
        "チャンネル登録と高評価、ぜひよろしくお願いします！ ✨",
        "うらうさまるのX(旧Twitter)もフォローしてくれると嬉しいです！",
        "次の配信もお楽しみに！通知をオンにして待っていてくださいね！",
    ]
    ANNOUNCEMENT_INTERVAL = 1800
    last_announcement_time = time.time()
    start_message = "うらうさまるchのアシスタントBOTです！ `!占い`や様々な質問にお答えできます。気軽に話しかけてくださいね！"
    send_message(youtube, live_chat_id, start_message)
    append_log("system", "Bot", start_message)
    seen_msg_ids = set()
    while True:
        try:
            current_time = time.time()
            if (current_time - last_announcement_time) > ANNOUNCEMENT_INTERVAL:
                announcement = random.choice(ANNOUNCEMENT_MESSAGES)
                send_message(youtube, live_chat_id, announcement)
                append_log("bot", "Bot", announcement)
                last_announcement_time = current_time
            if is_live_ended(youtube, video_id):
                end_message = "🎤 配信おつかれさまでした！また次回お会いしましょう！"
                send_message(youtube, live_chat_id, end_message)
                append_log("system", "Bot", end_message)
                logging.info("配信終了を検出。Bot停止。")
                shared_state.CURRENT_LIVE_CHAT_ID = None
                shared_state.CURRENT_VIDEO_ID = None
                break
            messages = poll_chat_messages(youtube, live_chat_id)
            for msg_id, author, text in messages:
                if msg_id in seen_msg_ids:
                    continue
                seen_msg_ids.add(msg_id)
                append_log("user", author, text)
                if text.startswith("!こんにちは"):
                    response_text = f"{author}さん、こんにちは！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)
                elif text.startswith("!今何時"):
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    response_text = f"{author}さん、今は {now} です！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)
                elif text.startswith("!占い"):
                    fortunes = [
                        "大吉 ✨",
                        "中吉 😊",
                        "小吉 🙂",
                        "吉 😉",
                        "末吉 🤔",
                        "凶 😥",
                        "大凶 😱",
                    ]
                    result = random.choice(fortunes)
                    response_text = f"{author}さんの今日の運勢は...【{result}】です！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)
                elif not text.startswith("!"):
                    ai_response = generate_response(text).strip()
                    if not ai_response:
                        ai_response = "すみません、うまくお答えできませんでした。"

                        full_response = f"{author}さん：{ai_response}"
                        logging.info(f"送信しようとしているメッセージ: {full_response}")
                        send_message(youtube, live_chat_id, full_response)
                append_log("bot", "Bot", full_response)

            time.sleep(5)
        except Exception as e:
            logging.exception(f"チャット監視エラー: {e}")
            time.sleep(10)
