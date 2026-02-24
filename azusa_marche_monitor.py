import requests
import os

# --- 設定：GitHubのSecretから読み込む ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def test_line():
    """LINEが届くかだけのテスト"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": "✅ LINE接続テスト：成功です！プログラムは正常に動いています。"}]
    }
    
    print("LINE送信を試みています...")
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        print("送信成功！LINEを確認してください。")
    except Exception as e:
        print(f"送信エラーが発生しました: {e}")
        if res:
            print(f"エラー詳細: {res.text}")

if __name__ == "__main__":
    test_line()
