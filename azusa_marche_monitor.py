import requests
import os
import re

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
TARGET_URL = "https://marche-yell.com/dst_miyaharaazu"

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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }
    
    try:
        # ショップページを直接読み込む
        response = requests.get(TARGET_URL, headers=headers)
        html = response.text
        
        # 【超重要】HTMLの中から商品名と在庫数を強引に抜き出す
        # 1. 商品タイトルを探す
        titles = re.findall(r'class="product-card__title">([^<]+)</div>', html)
        # 2. 「残り〇枚」の数字を探す
        stocks = re.findall(r'残り\s*(\d+)\s*枚', html)

        if not titles:
            print("商品タイトルが見つかりませんでした。構造を再確認します。")
            # デバッグ用に少し中身を出す
            print(html[:500])
            return

        print(f"{len(titles)}件の商品を見つけました。")

        for i in range(len(titles)):
            title = titles[i].strip()
            # 在庫数が取得できなかった場合は0とする
            remaining = int(stocks[i]) if i < len(stocks) else 0
            
            # --- 通知判定 ---
            # テスト用に一旦「True」にしています。成功したら remaining <= 3 に戻してください。
            if True:
                msg = f"\n【在庫チェック】宮原梓\n{title}\n残り {remaining} 枚\n{TARGET_URL}"
                send_line(msg)
                print(f"通知送信完了: {title} (残り{remaining}枚)")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_marche()
