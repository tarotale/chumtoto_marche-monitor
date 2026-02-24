import requests
import os
import re

# --- 設定：GitHubのSecretから読み込む ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
# APIではなく、通常のショップページを見に行きます
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        # HTMLの中から在庫情報を探す（簡易的な解析）
        html_content = response.text
        
        # 商品名と残り枚数を探す（サイトの構造に合わせた抽出）
        # ※正規表現で「残り◯枚」という部分を抜き出します
        items = re.findall(r'class="product-card__title">(.*?)<.*?残り\s*(\d+)\s*枚', html_content, re.S)
        
        if not items:
            print("商品データが見つかりませんでした。ページ構造が変わった可能性があります。")
            # デバッグ用にHTMLの一部を表示
            print(html_content[:500])
            return

        for title, remaining in items:
            remaining = int(remaining)
            title = title.strip()
            
            # テスト用に一旦「True」にしています。成功したら条件を戻してください。
            if True: 
                msg = f"\n【在庫チェック】宮原梓\n{title}\n残り {remaining} 枚\n{TARGET_URL}"
                send_line(msg)
                print(f"通知送信: {title}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_marche()
