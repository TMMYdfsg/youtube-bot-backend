# gemini/responder.py  (シンプルな会話AIに戻したバージョン)

import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def generate_response(prompt: str) -> str:
    """
    Geminiを使って、自由な質問に対して返答を生成する
    """
    try:
        # AIへのキャラクター設定は行わず、純粋にユーザーのプロンプトに応答を生成させる
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "すみません、現在応答できません。"
