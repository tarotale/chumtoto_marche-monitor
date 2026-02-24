import requests
import os

# --- 設定：GitHubのSecretから読み込む ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
API_URL = "https://marche-yell.com/api/v1/creators/dst_miyaharaazu/products"

def send_line(text):
    """LINE Messaging APIでプッシュ通知を送る"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def check_marche():
    """マルシェの在庫をチェックする"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://marche-yell.com/dst_miyaharaazu",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        products = response.json()
        
        for p in products:
            title = p.get('title', '新着商品')
            sold = p.get('sold_quantity', 0)
            limit = p.get('limit_quantity', 0)
            remaining = limit - sold
            p_id = p.get('id')
            p_url = f"https://marche-yell.com/dst_miyaharaazu/products/{p_id}"

            # 今回はシンプルに「在庫が3枚以下」になったら通知する設定です
            # ※もっと細かく（1枚売れるたび等）したい場合は、
            # データの保存が必要になるのでまずはここから！
            if True:  # テスト送信用：常に通知する
                msg = f"\n【在庫わずか！】宮原梓\n{title}\n残り {remaining} / {limit} 枚\n{p_url}"
                send_line(msg)
                print(f"通知送信: {title}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_marche()
