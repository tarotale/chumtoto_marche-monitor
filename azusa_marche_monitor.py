import requests
import os

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
API_URL = "https://marche-yell.com/api/v1/products?limit=50&order=new"
TARGET_CREATOR_ID = "dst_miyaharaazu"

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": text}]}
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def check_marche():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://marche-yell.com/"
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            return

        all_products = response.json()
        my_products = [p for p in all_products if p.get('creator_id') == TARGET_CREATOR_ID]
# --- ここからテスト用に追加 ---
        # 商品が空っぽの場合、テスト用のデータを1つ入れる
        if not my_products:
            my_products = [{
                'title': 'テスト送信（接続確認OK）',
                'limit_quantity': 10,
                'sold_quantity': 9,
                'id': 'test'
            }]
        # --- ここまでテスト用 ---
        for p in my_products:
            title = p.get('title', '新着商品')
            limit = p.get('limit_quantity', 0)
            sold = p.get('sold_quantity', 0)
            remaining = limit - sold
            p_id = p.get('id')
            p_url = f"https://marche-yell.com/dst_miyaharaazu/products/{p_id}"

            # 【自動監視条件】在庫が3枚以下、かつ0枚（完売）ではない時に通知
            if remaining <= 3 and remaining > 0:
                msg = f"\n【在庫わずか！】宮原梓\n{title}\n残り {remaining} / {limit} 枚\n{p_url}"
                send_line(msg)
                print(f"通知送信: {title}")

    except Exception as e:
        print(f"チェック失敗（出品待ち）: {e}")

if __name__ == "__main__":
    check_marche()
