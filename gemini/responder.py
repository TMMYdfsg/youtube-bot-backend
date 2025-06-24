# gemini/responder.py (f-stringの文法エラーを修正した最終版)

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

def analyze_user_comments(comments: list[str]) -> str:
    """
    特定のユーザーのコメントリストを受け取り、その傾向を分析・要約する
    """
    if not comments:
        return "分析対象のコメントがありません。"

    # ★★★ f-stringの文法エラーを修正 ★★★
    # まず、コメントリストを改行で連結した文字列を作成します
    comment_list_str = "\n- ".join(comments)

    # AIへの専門的な命令（プロンプト）
    analysis_prompt = f"""
    あなたは、YouTube配信のコメントを分析する専門のアナリストです。
    以下のコメントリストは、ある一人のユーザーが過去に行った発言です。
    これらの発言全体から、このユーザーの「興味の傾向」「口癖」「よく使う言葉」「ポジティブ/ネガティブな傾向」などを分析し、
    その人物像を3〜4行程度の短いレポートにまとめてください。

    # コメントリスト:
- {comment_list_str}
    """
    try:
        response = model.generate_content(analysis_prompt)
        return response.text.strip()
    except Exception as e:
        return f"AIによる分析中にエラーが発生しました: {e}"
