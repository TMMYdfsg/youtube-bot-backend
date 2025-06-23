# tests/test_youtube_api.py
import pytest
from youtube.chat import send_message


def test_send_message(mocker):
    """
    YouTubeチャットにメッセージを送信する関数のテスト
    """
    # YouTube APIサービス全体をモック化
    mock_youtube_service = mocker.Mock()

    # テスト対象の関数を実行
    live_chat_id = "test_chat_id"
    text = "テストメッセージ"
    send_message(mock_youtube_service, live_chat_id, text)

    # 検証：APIのinsertメソッドが正しい引数で1回呼び出されたか
    mock_youtube_service.liveChatMessages.assert_called_once()
    mock_youtube_service.liveChatMessages().insert.assert_called_once_with(
        part="snippet",
        body={
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text},
            }
        },
    )
    mock_youtube_service.liveChatMessages().insert().execute.assert_called_once()
