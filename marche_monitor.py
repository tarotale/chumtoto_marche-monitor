import requests
import os
import json
import re

# --- 設定 ---
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
DB_FILE = "last_stock.json"

TARGET_CREATORS = [
    {"name": "宮原梓", "id": "dst_miyaharaazu"},
    {"name": "江本夏渚", "id": "dst_emotonana"},
    {"name": "柏葉れん", "id": "dst_kashiwabare"},
    {"name": "瀬﨑くるみ", "id": "dst_sezakikurum"},
    {"name": "詩之宮かこ", "id": "chum_shinomiyak"},
    {"name": "ChumToto", "id": "chumtoto"},
]

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    payload = {"to": USER_ID, "messages": [{"type": "text", "text": text}]}
    requests.post(url, headers=headers, json=payload)

def get_product_detail(cid, p_id):
    """特定の商品ページを見に行って在庫数を正確に取る"""
    url = f"https://marche-yell.com/{cid}/products/{p_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
        if json_match:
            data = json.loads(json_match.group(1))
            p = data.get('props', {}).get('pageProps', {}).get('product', {})
            if p:
                limit = p.get('limit_quantity', 0)
                sold = p.get('sold_quantity', 0)
                return p.get('title'), limit - sold, limit
    except:
        pass
    return None, 0, 0

def check_marche():
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: last_data = json.load(f)

    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"}
    current_all_data = {}

    for creator in TARGET_CREATORS:
        cid = creator["id"]
        print(f"チェック中: {creator['name']}...")
        
        # 1. 一覧ページから「商品ID」の羅列だけを抜き出す（ここはブロックされにくい）
        res = requests.get(f"https://marche-yell.com/{cid}", headers=headers)
        # ID（数字6桁前後）をすべて見つける
        found_ids = list(set(re.findall(r'/products/(\d+)', res.text)))
        
        current_all_data[cid] = found_ids
        old_ids = last_data.get(cid, [])

        # 2. 前回いなかった「新しいID」があれば、詳細ページへ中身を見に行く
        for p_id in found_ids:
            if p_id not in old_ids:
                title, remaining, limit = get_product_detail(cid, p_id)
                if title and remaining > 0:
                    msg = f"\n✨【新着】{creator['name']}\n{title}\n在庫：残り {remaining} / 全 {limit} 枚\nhttps://marche-yell.com/{cid}/products/{p_id}"
                    send_line(msg)
                    print(f"  -> 新商品を検知: {title}")

    with open(DB_FILE, "w") as f: json.dump(current_all_data, f)

if __name__ == "__main__":
    check_marche()
