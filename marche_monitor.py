import requests
import json
import os
import time
from datetime import datetime, timedelta

# --- 設定 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

# --- 修正版：あだ名付きターゲットリスト ---
TARGET_CREATORS = [
    {"name": "宮原梓", "id": "dst_miyaharaazu", "nickname": "ずに|あずさ|梓|あずにゃん|あずにゃ|みゃずさ|みやはら"},
    {"name": "江本夏渚", "id": "dst_emotonana", "nickname": "えもと|なな|ななちゃん|えもなな|エモ(となな)"},
    {"name": "柏葉れん", "id": "dst_kashiwabare", "nickname": "れん|れんちゃん|かし|カシ|ドム|ジオング|かしわば"},
    {"name": "瀬﨑くるみ", "id": "dst_sezakikurum", "nickname": "陶芸家|くるみん|せざき|せざくる|セザクル"},
    {"name": "詩之宮かこ", "id": "chum_shinomiyak", "nickname": "かこちゃん|かこちま|ちま|かこち|しのみや"},
    {"name": "ChumToto", "id": "chumtoto", "nickname": "ちゅむとと|公式"},
]

DB_FILE = "chum_last_inventory.json"

def convert_to_jst_full(utc_str):
    """UTCを日本時間(YYYY-MM-DD HH:MM)に変換"""
    if not utc_str: return "0000-00-00 00:00"
    try:
        dt_utc = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        dt_jst = dt_utc + timedelta(hours=9)
        return dt_jst.strftime("%Y-%m-%d %H:%M")
    except:
        return "0000-00-00 00:00"

def send_line(message):
    if not LINE_TOKEN:
        print("LINE_TOKENが設定されていないため、送信をスキップします。")
        return
    
    # 送信先をブロードキャスト（全員）用のエンドポイントに変更
    url = "https://api.line.me/v2/bot/message/broadcast"
    
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    
    # 'to' (宛先) 指定が不要になります
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        print(f"一斉配信成功: {message[:20]}...")
    except Exception as e:
        print(f"LINE送信エラー: {e}")
def main():
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            last_data = json.load(f)

    new_inventory_data = last_data.copy()

    for creator in TARGET_CREATORS:
        c_name = creator["name"]
        c_id = creator["id"]
        
        print(f"--- 監視中: {c_name} ({c_id}) ---")
        list_api = f"https://api.marche-yell.com/api/public/products?creator_marche_id={c_id}&limit=100"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://marche-yell.com",
            "Referer": f"https://marche-yell.com/{c_id}/"
        }

        try:
            res = requests.get(list_api, headers=headers, timeout=15)
            res.raise_for_status()
            products = res.json().get('products', [])
            
            for p in products:
                p_id = str(p.get('id'))
                title = p.get('title', '不明')
                start_jst = convert_to_jst_full(p.get('sales_start_at'))
                
                limit = p.get('limit_quantity', 0)
                sold = p.get('sold_quantity', 0)
                stock = limit - sold
                
                db_key = f"{c_id}_{p_id}"
                
                # 現在の日本時間を取得
                now_jst = datetime.now(timedelta(hours=9))
                
                # 商品の開始時間を比較用に変換
                try:
                    start_dt = datetime.strptime(start_jst, "%Y-%m-%d %H:%M")
                    # 簡易的な比較のため、JSTの時間を生成
                    is_future = start_dt > now_jst.replace(tzinfo=None)
                except:
                    is_future = False

                msg = ""
                # 1. 完全な新着
                if db_key not in last_data:
                    msg = (f"✨【新着】{c_name}\n"
                           f"📝 {title}\n"
                           f"📅 開始: {start_jst}\n"
                           f"📦 在庫: {stock}/{limit}\n")
                    
                    if is_future:
                        msg += f"🔗 https://marche-yell.com/{c_id}/products/{p_id}" # 未来ならURL
                    else:
                        msg += f"🆔 商品ID: {p_id}" # 過去ならID

                # 2. 在庫復活
                elif stock > 0 and last_data[db_key].get('stock', 0) == 0:
                    msg = (f"🔄【復活】{c_name}\n"
                           f"📝 {title}\n"
                           f"📦 残り {stock}個！\n")
                    
                    if is_future:
                        msg += f"🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                    else:
                        msg += f"🆔 商品ID: {p_id}"

                # 通知送信
                if msg:
                    send_line(msg)
                    print(f"通知送信: {title} (Future: {is_future})")
                # JSON保存用のデータ更新（ここは常に最新にする）
                new_inventory_data[db_key] = {
                    "name": c_name,
                    "title": title, 
                    "stock": stock, 
                    "limit": limit,
                    "start": start_jst,
                    "creator_id": c_id
                }

        except Exception as e:
            print(f"エラー ({c_name}): {e}")

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(new_inventory_data, f, ensure_ascii=False, indent=2)
    print(f"JSON更新完了: {DB_FILE}")

if __name__ == "__main__":
    main()
