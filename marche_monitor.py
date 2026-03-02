import requests
import json
import os
from datetime import datetime, timedelta

# --- 設定 ---
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
DB_FILE = "chum_last_inventory.json"

TARGET_CREATORS = [
    {"name": "宮原梓", "id": "dst_miyaharaazu", "nickname": "ずに|あずさ|梓|あずにゃん|あずにゃ|みゃずさ|みやはら"},
    {"name": "江本夏渚", "id": "dst_emotonana", "nickname": "えもと|なな|ななちゃん|えもなな|エモ(となな)|エモ"},
    {"name": "柏葉れん", "id": "dst_kashiwabare", "nickname": "れん|れんちゃん|かし|カシ|ドム|ジオング|かしわば"},
    {"name": "瀬﨑くるみ", "id": "dst_sezakikurum", "nickname": "陶芸家|くるみん|せざき|せざくる|セザクル"},
    {"name": "詩之宮かこ", "id": "chum_shinomiyak", "nickname": "かこちゃん|かこちま|ちま|かこち|しのみや"},
    {"name": "ChumToto", "id": "chumtoto", "nickname": "ちゃむとと|公式|ちゃむ|チャムトト"},
]

def convert_to_jst_full(utc_str):
    if not utc_str: return "0000-00-00 00:00"
    try:
        dt_utc = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        dt_jst = dt_utc + timedelta(hours=9)
        return dt_jst.strftime("%Y-%m-%d %H:%M")
    except:
        return "0000-00-00 00:00"

def send_line(message):
    if not LINE_TOKEN: return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    payload = {"messages": [{"type": "text", "text": message}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    # 既存のデータを読み込む（通知の判定に必要）
    last_data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                last_data = json.load(f)
            except:
                last_data = {}

    # 今回の全データを保持するための辞書（読み込んだ既存データで初期化）
    # これにより、APIから消えた古いデータも保持されます
    current_all_data = last_data.copy()

    for creator in TARGET_CREATORS:
        c_name = creator["name"]
        c_id = creator["id"]
        c_nickname = creator["nickname"]
        
        print(f"--- 取得中: {c_name} ---")
        # limit=100で多めに取得
        list_api = f"https://api.marche-yell.com/api/public/products?creator_marche_id={c_id}&limit=100"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

        try:
            res = requests.get(list_api, headers=headers, timeout=15)
            res.raise_for_status()
            products = res.json().get('products', [])
            
            for p in products:
                p_id = str(p.get('id'))
                title = p.get('title', '不明')
                start_jst = convert_to_jst_full(p.get('sales_start_at'))
                limit = p.get('limit_quantity', 0)
                stock = limit - p.get('sold_quantity', 0)
                db_key = f"{c_id}_{p_id}"
                
                # 通知メッセージ作成
                msg = ""
                if db_key not in last_data:
                    msg = f"✨【新着】{c_name}\n📝 {title}\n📅 開始: {start_jst}\n📦 在庫: {stock}/{limit}\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                elif stock > 0 and last_data[db_key].get('stock', 0) == 0:
                    msg = f"🔄【復活】{c_name}\n📝 {title}\n📦 残り {stock}個！\n🔗 https://marche-yell.com/{c_id}/products/{p_id}"
                
                if msg:
                    send_line(msg)

                # 最新の情報をセット（既存のものがあれば上書き、なければ新規追加）
                # nicknameを常に最新のターゲットリストから反映
                current_all_data[db_key] = {
                    "name": c_name,
                    "nickname": c_nickname,
                    "title": title, 
                    "stock": stock, 
                    "limit": limit,
                    "start": start_jst,
                    "creator_id": c_id
                }

        except Exception as e:
            print(f"エラー ({c_name}): {e}")

    # 最後にDB_FILEを丸ごと上書き保存
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(current_all_data, f, ensure_ascii=False, indent=2)
    print(f"JSONを最新状態で上書き完了しました。全データ保持されています。")

if __name__ == "__main__":
    main()
