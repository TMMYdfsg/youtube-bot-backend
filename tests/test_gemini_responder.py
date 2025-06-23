# tests/test_gemini_responder.py
import pytest
from gemini.responder import generate_response


def test_generate_response_success(mocker):
    """
    Geminiが正常に応答を返した場合のテスト
    """
    # mockerを使って、実際のAPI呼び出しを偽の応答に置き換える
    mock_response = mocker.Mock()
    mock_response.text = "こんにちは！"

    mock_model = mocker.patch("gemini.responder.model.generate_content")
    mock_model.return_value = mock_response

    # テスト対象の関数を実行
    result = generate_response("テストプロンプト")

    # 検証：期待通りの応答が返ってくるか
    assert result == "こんにちは！"
    # 検証：APIが1回だけ呼ばれたか
    mock_model.assert_called_once_with("テストプロンプト")


def test_generate_response_error(mocker):
    """
    Gemini APIでエラーが発生した場合のテスト
    """
    # API呼び出しが例外を発生させるように設定
    mock_model = mocker.patch("gemini.responder.model.generate_content")
    mock_model.side_effect = Exception("API Error")

    # テスト対象の関数を実行
    result = generate_response("エラーになるプロンプト")

    # 検証：エラー時に定義したメッセージが返ってくるか
    assert result == "すみません、現在応答できません。"
