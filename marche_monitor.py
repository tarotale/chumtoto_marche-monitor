import requests
import json
import os
import re
from datetime import datetime, timedelta
import time

# --- 設定 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
DB_FILE = "chum_last_inventory.json"

# メンバー情報（ニックネーム・カラー・ID）
TARGET_CREATORS = [
    {"name": "宮原梓", "id": "dst_miyaharaazu", "emoji": "🤍", "nickname": "ずに|あずさ|梓|あずにゃん|あずにゃ|みゃずさ|みやはら"},
    {"name": "江本夏渚", "id": "dst_emotonana", "emoji": "❤️", "nickname": "えもと|なな|ななちゃん|えもなな|エモ\(となな\)|江本|エモ"},
    {"name": "柏葉れん", "id": "dst_kashiwabare", "emoji": "🩵", "nickname": "れん|れんちゃん|かし|カシ|ドム|ジオング|かしわば"},
    {"name": "瀬﨑くるみ", "id": "dst_sezakikurum", "emoji": "🩷", "nickname": "陶芸家|くるみん|せざき|せざくる|セザクル"},
    {"name": "詩之宮かこ", "id": "chum_shinomiyak", "emoji": "💛", "nickname": "かこちゃん|かこちま|ちま|かこち|しのみや"},
    {"name": "ChumToto", "id": "chumtoto", "emoji": "🍭", "nickname": "公式|チャムトト"},
]

def find_creator_by_nickname(text):
    """
    入力されたテキストからニックネームを照合してメンバー情報を返す
    (Webhook応答機能の実装時に使用可能)
    """
    for creator in TARGET_CREATORS:
        if re.search(creator["nickname"], text):
            return creator
    return None

def convert_to_jst_full(utc_str):
    if not utc_str: return "0000-00-00 00:00"
    try:
        dt_utc = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        dt_jst = dt_utc + timedelta(hours=9)
        return dt_jst.strftime("%Y-%m-%d %H:%M")
    except:
        return "0000-00-00 00:00"

def send_line(message):
    """
    LINE Messaging APIを使用してメッセージを配信
    """
    if not LINE_TOKEN:
        print("Error: LINE_ACCESS_TOKEN is not set.")
        return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    last_data = {}
    # 既存データの読み込み
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                last_data = json.load(f)
            except:
                last_data = {}

    current_all_data = last_data.copy()

    for creator in TARGET_CREATORS:
        c_name = creator["name"]
        c_id = creator["id"]
        c_emoji = creator["emoji"]
        
        # メンバーごとに全件取得（ページネーション対応）
        offset = 0
        while True:
            list_api = f"https://api.marche-yell.com/api/public/products?creator_marche_id={c_id}&limit=100&offset={offset}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            
            try:
                res = requests.get(list_api, headers=headers, timeout=15)
                res.raise_for_status()
                products = res.json().get('products', [])
                
                if not products:
                    break
                
                for p in products:
                    p_id = str(p.get('id'))
                    title = p.get('title', '不明')
                    start_jst = convert_to_jst_full(p.get('sales_start_at'))
                    limit = p.get('limit_quantity', 0)
                    sold = p.get('sold_quantity', 0)
                    stock = limit - sold
                    db_key = f"{c_id}_{p_id}"
                    
                    msg = ""
                    # 新着検知
                    if db_key not in last_data:
                        msg = f"🍭【ChumToto/新着】{c_emoji}{c_name}\n📝 {title}\n📅 開始: {start_jst}\n📦 在庫: {stock}/{limit}\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                    # 復活検知（在庫が0から復活した場合）
                    elif stock > 0 and last_data[db_key].get('stock', 0) == 0:
                        msg = f"🔄【ChumToto/復活】{c_emoji}{c_name}\n📝 {title}\n📦 残り {stock}個！\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                    
                    if msg:
                        send_line(msg)

                    # データベース更新用の辞書
                    current_all_data[db_key] = {
                        "name": c_name,
                        "title": title, 
                        "stock": stock, 
                        "limit": limit,
                        "start": start_jst,
                        "creator_id": c_id
                    }
                
                # 100件未満なら終了
                if len(products) < 100:
                    break
                
                offset += 100
                time.sleep(1) # API負荷軽減
                
            except Exception as e:
                print(f"Error ({c_name}): {e}")
                break

    # 最終データをファイルに保存
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(current_all_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
