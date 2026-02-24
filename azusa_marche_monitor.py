import requests
import os

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
# URLを少し変え、フィルタリングを外した状態のAPIを叩きます
API_URL = "https://marche-yell.com/api/v1/creators/dst_miyaharaazu/products"

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
    # セッション（ブラウザのふり）を開始
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Referer": "https://marche-yell.com/dst_miyaharaazu",
        "Connection": "keep-alive",
    }
    
    try:
        # 1. まずはトップページに一度アクセスして「足跡（Cookie）」を残す
        session.get("https://marche-yell.com/dst_miyaharaazu", headers=headers)
        
        # 2. その足跡を持ったまま、APIにデータを貰いに行く
        response = session.get(API_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}") # 届いた文字数を表示
        
        if not response.text.strip():
            print("サーバーから空の応答が返ってきました。アクセス制限の可能性があります。")
            return

        products = response.json()
        
        for p in products:
            title = p.get('title', '商品')
            limit = p.get('limit_quantity', 0)
            sold = p.get('sold_quantity', 0)
            remaining = limit - sold
            p_id = p.get('id')
            p_url = f"https://marche-yell.com/dst_miyaharaazu/products/{p_id}"

            # テスト用に常に通知
            if True:
                msg = f"\n【在庫チェック】宮原梓\n{title}\n残り {remaining} 枚\n{p_url}"
                send_line(msg)
                print(f"通知送信完了: {title}")

    except Exception as e:
        print(f"エラー発生: {e}")
        # もし中身がJSONじゃない場合は、その中身を少し表示して原因を探る
        if 'response' in locals():
            print(f"受信した内容の冒頭: {response.text[:100]}")

if __name__ == "__main__":
    check_marche()
