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
    messages = (
        youtube.liveChatMessages()
        .list(liveChatId=live_chat_id, part="snippet,authorDetails")
        .execute()
    )
    result = []
    for item in messages["items"]:
        msg_id = item["id"]
        text = item["snippet"]["textMessageDetails"]["messageText"]
        author = item["authorDetails"]["displayName"]
        result.append((msg_id, author, text))
    return result


def send_message(youtube, live_chat_id, text):
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
