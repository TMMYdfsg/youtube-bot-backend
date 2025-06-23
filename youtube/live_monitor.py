import time
import datetime
import logging
from youtube.auth import get_authenticated_service
from youtube.chat import get_live_chat_id, poll_chat_messages, send_message
from gemini.responder import generate_response
from config import TARGET_CHANNEL_ID


def monitor_live_stream():
    youtube = get_authenticated_service()
    live_chat_id, video_id = get_live_chat_id(youtube, TARGET_CHANNEL_ID)

    if not live_chat_id:
        logging.info("ライブ配信なし。リトライします...")
        time.sleep(30)
        return

    logging.info(f"ライブ検出: VideoID={video_id}")
    send_message(youtube, live_chat_id, "🎉 Botが参加しました！こんにちは！")

    seen_msg_ids = set()

    while True:
        try:
            # ✅ 配信が終了していないか確認
            if is_live_ended(youtube, video_id):
                send_message(
                    youtube,
                    live_chat_id,
                    "🎤 配信おつかれさまでした！また次回お会いしましょう！",
                )
                logging.info("配信終了を検出。Bot停止。")
                break

            # チャット取得＆応答処理
            messages = poll_chat_messages(youtube, live_chat_id)
            for msg_id, author, text in messages:
                if msg_id in seen_msg_ids:
                    continue
                seen_msg_ids.add(msg_id)

                if text.startswith("!こんにちは"):
                    send_message(youtube, live_chat_id, f"{author}さん、こんにちは！")
                elif text.startswith("!今何時"):
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    send_message(
                        youtube, live_chat_id, f"{author}さん、今は {now} です！"
                    )
                else:
                    response = generate_response(text)
                    send_message(youtube, live_chat_id, f"{author}さん：{response}")

            time.sleep(5)

        except Exception as e:
            logging.exception(f"チャット監視エラー: {e}")
            time.sleep(10)


def is_live_ended(youtube, video_id: str) -> bool:
    """
    ライブ配信が終了しているか確認
    Returns True if live has ended
    """
    try:
        video_details = (
            youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
        )

        details = video_details["items"][0]["liveStreamingDetails"]
        end_time = details.get(
            "actualEndTime"
        )  # ISO8601形式: e.g. 2024-06-24T12:45:00Z

        return end_time is not None
    except Exception as e:
        logging.warning(f"終了チェック中にエラー: {e}")
        return False

chat_log_cache = []


def append_log(author: str, text: str, response: str):
    chat_log_cache.append(
        {
            "author": author,
            "message": text,
            "response": response,
            "timestamp": datetime.datetime.now().isoformat(),
        }
    )
    if len(chat_log_cache) > 50:
        chat_log_cache.pop(0)


def get_latest_logs():
    return chat_log_cache
