def get_live_chat_id(youtube, channel_id):
    search_response = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        eventType="live",
        type="video"
    ).execute()

    if not search_response.get("items"):
        print("[デバッグ] ライブ配信が見つかりません。")
        return None, None

    video_id = search_response["items"][0]["id"]["videoId"]
    print(f"[デバッグ] ライブVideo ID: {video_id}")

    video_response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()

    items = video_response.get("items", [])
    if not items or "liveStreamingDetails" not in items[0]:
        print("[デバッグ] liveStreamingDetailsが取得できません。")
        return None, None

    live_chat_id = items[0]["liveStreamingDetails"].get("activeLiveChatId")
    print(f"[デバッグ] liveChatId: {live_chat_id}")
    return live_chat_id, video_id
