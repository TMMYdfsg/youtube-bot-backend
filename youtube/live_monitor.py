# youtube/live_monitor.py

import random
import time
import datetime
import logging
import sqlite3
from youtube.auth import get_authenticated_service
from youtube.chat import get_live_chat_id, poll_chat_messages, send_message
import shared_state
from config import TARGET_CHANNEL_ID
from gemini.responder import generate_response, analyze_user_comments
from database import DATABASE_FILE, get_recent_comments_by_user

def is_live_ended(youtube, video_id: str) -> bool:
    try:
        video_details = youtube.videos().list(
            part="liveStreamingDetails", id=video_id).execute()
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

def get_time_based_greeting():
    now = datetime.datetime.now()
    hour = now.hour
    weekday = now.weekday()
    if hour < 12:
        time_greeting = "おはようございます☀"
    elif hour < 18:
        time_greeting = "こんにちは☀"
    else:
        time_greeting = "こんばんは🌙"
    weekday_str = ["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"][weekday]
    return f"{time_greeting} {weekday_str}の配信、今日もよろしくお願いします！"

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

    # 開始時あいさつ（時間と曜日で変化）
    start_message = get_time_based_greeting() + " アシスタントBOTです！ `/占い` や `/分析` など気軽にどうぞ！"
    send_message(youtube, live_chat_id, start_message)
    append_log("system", "Bot", start_message)

    ANNOUNCEMENT_MESSAGES = [
        "チャンネル登録と高評価、ぜひよろしくお願いします！✨",
        "うらうさまるのX(旧Twitter)もフォローしてくれると嬉しいです！",
        "次の配信もお楽しみに！通知をオンにして待っていてくださいね！",
    ]
    ANNOUNCEMENT_INTERVAL = 1800  # 30分
    last_announcement_time = time.time()
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

                if text.startswith("/こんにちは"):
                    response_text = f"{author}さん、こんにちは！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)

                elif text.startswith("/今何時"):
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    response_text = f"{author}さん、今は {now} です！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)

                elif text.startswith("/占い"):
                    fortunes = ["大吉 ✨", "中吉 😊", "小吉 🙂", "吉 😉", "末吉 🤔", "凶 😥", "大凶 😱"]
                    result = random.choice(fortunes)
                    response_text = f"{author}さんの今日の運勢は...【{result}】です！"
                    send_message(youtube, live_chat_id, response_text)
                    append_log("bot", "Bot", response_text)

                elif text.startswith("/分析"):
                    parts = text.split()
                    if len(parts) >= 2:
                        target_user = parts[1]
                        comments = get_recent_comments_by_user(target_user)
                        if not comments:
                            response = f"{target_user}さんのコメントが見つかりませんでした。"
                        else:
                            response = analyze_user_comments(comments)
                        send_message(youtube, live_chat_id, response)
                        append_log("bot", "Bot", response)
                    else:
                        help_msg = "使い方：`/分析 ユーザー名` でその人の発言傾向を分析できます。"
                        send_message(youtube, live_chat_id, help_msg)
                        append_log("bot", "Bot", help_msg)

                elif not text.startswith("/"):
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
