# youtube/chat.py

import logging


def get_live_chat_id(youtube, channel_id):
    search_response = (
        youtube.search()
        .list(part="id", channelId=channel_id, eventType="live", type="video")
        .execute()
    )
    if not search_response.get("items"):
        return None, None

    video_id = search_response["items"][0]["id"]["videoId"]
    video_response = (
        youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
    )

    details = video_response["items"][0]["liveStreamingDetails"]
    return details.get("activeLiveChatId"), video_id


def poll_chat_messages(youtube, live_chat_id):
    response = (
        youtube.liveChatMessages()
        .list(liveChatId=live_chat_id, part="snippet,authorDetails")
        .execute()
    )

    result = []
    for item in response.get("items", []):
        msg_id = item["id"]
        snippet = item.get("snippet", {})
        author = item["authorDetails"]["displayName"]

        # 💡 テキストメッセージ以外（スタンプ等）を除外
        text_details = snippet.get("textMessageDetails")
        if not text_details:
            continue

        text = text_details.get("messageText", "")
        logging.info(
            f"[チャット受信] {author}: {text} (msg_id={msg_id})"
        )  # ← ここでログ確認
        result.append((msg_id, author, text))
    return result


def send_message(youtube, live_chat_id, text):
    if not text or not isinstance(text, str):
        text = "（応答が生成できませんでした）"

    # 改行や制御文字を取り除く
    text = text.replace("\n", " ").replace("\r", " ").strip()

    # 長さ制限（YouTubeチャットは200文字上限）
    if len(text) > 200:
        text = text[:197] + "..."

    logging.info(f"[send_message] 送信内容: {text}")

    youtube.liveChatMessages().insert(
        part="snippet",
        body={
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text},
            }
        },
    ).execute()
