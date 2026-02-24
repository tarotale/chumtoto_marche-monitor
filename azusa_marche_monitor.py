import requests
import os
import json
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # 1. ページ本体を取得
        response = requests.get(TARGET_URL, headers=headers)
        html = response.text

        # 2. HTMLの奥底に眠る「__NEXT_DATA__」というJSONを探し出す
        # マルシェは画面表示用の全データをこの中に隠しています
        json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        
        if not json_match:
            print("データタグ（__NEXT_DATA__）が見つかりません。")
            print(f"取得したHTMLの長さ: {len(html)}")
            return

        # 3. JSONを解析して商品データまで潜り込む
        full_data = json.loads(json_match.group(1))
        
        # 階層が深いので、安全に一つずつ辿ります
        props = full_data.get('props', {})
        page_props = props.get('pageProps', {})
        # 商品リストはここにあるはず
        products = page_props.get('products', [])

        if not products:
            print("データタグは見つかりましたが、商品リストが空でした。")
            return

        print(f"{len(products)}件の商品データを抽出しました。")

        for p in products:
            title = p.get('title', '新着商品')
            limit = p.get('limit_quantity', 0)
            sold = p.get('sold_quantity', 0)
            remaining = limit - sold
            p_id = p.get('id')
            p_url = f"https://marche-yell.com/dst_miyaharaazu/products/{p_id}"

            # テスト用に一旦「True」にしています。成功したら条件を戻してください。
            if True:
                msg = f"\n【在庫チェック】宮原梓\n{title}\n残り {remaining} 枚\n{p_url}"
                send_line(msg)
                print(f"通知送信完了: {title}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    check_marche()
