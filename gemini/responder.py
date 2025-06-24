# gemini/responder.py

import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_response(prompt: str) -> str:
    """通常の会話応答を生成する"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "すみません、現在応答できません。"

# ★★★ ユーザー分析専用の関数を新しく追加 ★★★
def analyze_user_comments(comments: list[str]) -> str:
    """
    特定のユーザーのコメントリストを受け取り、その傾向を分析・要約する
    """
    if not comments:
        return "分析対象のコメントがありません。"

    # AIへの専門的な命令（プロンプト）
    analysis_prompt = f"""
    あなたは、YouTube配信のコメントを分析する専門のアナリストです。
    以下のコメントリストは、ある一人のユーザーが過去に行った発言です。
    これらの発言全体から、このユーザーの「興味の傾向」「口癖」「よく使う言葉」「ポジティブ/ネガティブな傾向」などを分析し、
    その人物像を3〜4行程度の短いレポートにまとめてください。

    # コメントリスト:
    - {"\n- ".join(comments)}
    """
    try:
        response = model.generate_content(analysis_prompt)
        return response.text.strip()
    except Exception as e:
        return f"AIによる分析中にエラーが発生しました: {e}"
