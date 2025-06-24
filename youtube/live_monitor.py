# youtube/live_monitor.py

import random
import time
import datetime
import logging
from youtube.auth import get_authenticated_service
from youtube.chat import get_live_chat_id, poll_chat_messages, send_message, is_live_ended
from gemini.responder import generate_response
from config import TARGET_CHANNEL_ID
from shared_state import shared_state  # ★★★ 1. 共有ファイルをインポート

def monitor_live_stream():
    youtube = get_authenticated_service()
    shared_state.YOUTUBE_SERVICE = youtube  # ★★★ 2. 共有ファイルにサービスを保存

    live_chat_id, video_id = get_live_chat_id(youtube, TARGET_CHANNEL_ID)

    if not live_chat_id:
        logging.info("ライブ配信なし。リトライします...")
        shared_state.CURRENT_LIVE_CHAT_ID = None  # ★★★ 3. 共有IDをクリア
        time.sleep(30)
        return

    shared_state.CURRENT_LIVE_CHAT_ID = live_chat_id  # ★★★ 4. 共有ファイルに現在のチャットIDを保存
    logging.info(f"ライブ検出: VideoID={video_id}")
    
    # 開始の挨拶
    start_message = "🎉 Botが参加しました！こんにちは！"
    send_message(youtube, live_chat_id, start_message)
    append_log("Bot", "（参加）", start_message) # ★★★ 5. ログを記録

    seen_msg_ids = set()

    while True:
        try:
            if is_live_ended(youtube, video_id):
                end_message = "🎤 配信おつかれさまでした！また次回お会いしましょう！"
                send_message(youtube, live_chat_id, end_message)
                append_log("Bot", "（終了）", end_message) # ★★★ 5. ログを記録
                logging.info("配信終了を検出。Bot停止。")
                shared_state.CURRENT_LIVE_CHAT_ID = None # ★★★ 3. 共有IDをクリア
                break

            messages = poll_chat_messages(youtube, live_chat_id)
            for msg_id, author, text in messages:
                if msg_id in seen_msg_ids:
                    continue
                seen_msg_ids.add(msg_id)
                
                response_text = "" # Botの返信を格納する変数

                if text.startswith("!こんにちは"):
                    response_text = f"{author}さん、こんにちは！"
                    send_message(youtube, live_chat_id, response_text)
                elif text.startswith("!今何時"):
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    response_text = f"{author}さん、今は {now} です！"
                    send_message(youtube, live_chat_id, response_text)
                elif text.startswith("!占い"): # ★★★ 6. !占いコマンドを追加
                    fortunes = ["大吉 ✨", "中吉 😊", "小吉 🙂", "吉 😉", "末吉 🤔", "凶 😥", "大凶 😱"]
                    result = random.choice(fortunes)
                    response_text = f"{author}さんの今日の運勢は...【{result}】です！"
                    send_message(youtube, live_chat_id, response_text)
                else:
                    response_text = generate_response(text)
                    send_message(youtube, live_chat_id, f"{author}さん：{response_text}")
                
                # Botが何か応答したら、その内容をログに記録
                if response_text:
                    append_log(author, text, response_text) # ★★★ 5. ログを記録

            time.sleep(5)

        except Exception as e:
            logging.exception(f"チャット監視エラー: {e}")
            time.sleep(10)


def is_live_ended(youtube, video_id: str) -> bool:
    try:
        video_details = (
            youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
        )
        if not video_details.get("items"):
            return True # 動画情報が取得できなければ終了とみなす
            
        details = video_details["items"][0]["liveStreamingDetails"]
        return details.get("actualEndTime") is not None
    except Exception as e:
        logging.warning(f"終了チェック中にエラー: {e}")
        return False # 不明なエラーの場合は続行させる

# 以下のログ関連の関数はそのまま
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
