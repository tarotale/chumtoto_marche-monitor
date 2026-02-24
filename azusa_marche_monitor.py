import requests
import os
import re
import json

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
TARGET_URL = "https://marche-yell.com/dst_miyaharaazu"
DB_FILE = "last_stock.json"

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
    # 前回データの読み込み
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            last_data = json.load(f)

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        html = response.text
        titles = re.findall(r'class="product-card__title">([^<]+)</div>', html)
        stocks = re.findall(r'残り\s*(\d+)\s*枚', html)

        current_data = {}
        for i in range(len(titles)):
            title = titles[i].strip()
            count = int(stocks[i])
            current_data[title] = count

            last_count = last_data.get(title, -1) # 初めて見る商品は-1

            # --- 通知判定 ---
            should_notify = False
            reason = ""

            if last_count == -1:
                # 新しく出品された！
                should_notify = True
                reason = "✨ 新着出品！"
            elif count <= 3 and last_count > 3:
                # 3枚以下になった瞬間！
                should_notify = True
                reason = "⚠️ 残りわずか！"
            elif count > last_count and last_count != -1:
                # 在庫が補充された！
                should_notify = True
                reason = "🔄 在庫復活！"

            if should_notify:
                msg = f"\n【{reason}】宮原梓\n{title}\n残り {count} 枚\n{TARGET_URL}"
                send_line(msg)
                print(f"通知送信: {title}")

        # 今回の状態を保存
        with open(DB_FILE, "w") as f:
            json.dump(current_data, f)

    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    check_marche()
