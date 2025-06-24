# test_app.py

from flask import Flask, jsonify
from flask_cors import CORS

# 非常にシンプルなFlaskアプリケーションを作成
app = Flask(__name__)

# CORSを有効化
CORS(app)


# /api/test という単一の窓口だけを用意
@app.route("/api/test")
def test_endpoint():
    # このAPIが呼ばれたら、ターミナルに成功メッセージを表示
    print(">>> /api/test endpoint was hit successfully!")
    return jsonify({"message": "最小構成サーバーからの応答です！"})


if __name__ == "__main__":
    # 必ずデバッグモードをオンで実行
    app.run(host="0.0.0.0", port=5000, debug=True)
# このファイルは、最小限のFlaskサーバーを起動するためのものです。
# これにより、APIの基本的な動作を確認できます。