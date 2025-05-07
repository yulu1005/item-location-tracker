import json
import time
from datetime import datetime, date
import google.generativeai as genai

# 初始化 Gemini 模型
genai.configure(api_key="自己的API")  # ⚠️ 請換成你自己的金鑰
model = genai.GenerativeModel("gemini-2.0-flash")

# ========== 對話記憶儲存與載入 ==========
CHAT_HISTORY_FILE = "chat_history.json"

def load_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []  # 空檔案視為空記憶
            raw = json.loads(content)
            return [{"role": m["role"], "parts": [m["text"]]} for m in raw]
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ chat_history.json 格式錯誤或不存在，已重設為空記憶。")
        return []

def save_chat_history(history):
    serializable_history = []
    for m in history:
        if hasattr(m, "role") and hasattr(m, "parts"):
            part = m.parts[0]
            if hasattr(part, "text"):
                text = part.text
            elif isinstance(part, str):
                text = part
            else:
                text = str(part)
            serializable_history.append({
                "role": m.role,
                "text": text
            })
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable_history, f, ensure_ascii=False, indent=2)

# 建立有記憶的對話 session
chat_session = model.start_chat(history=load_chat_history())

# ========== Gemini 安全生成內容 ==========
def safe_generate(prompt):
    try:
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        if "429" in str(e):
            print("⚠️ 達到API限制，等待60秒後重試...")
            time.sleep(60)
            try:
                return model.generate_content(prompt).text.strip()
            except Exception as e2:
                print("再次失敗：", e2)
                return None
        else:
            print("呼叫錯誤：", e)
            return None

# ========== 資料儲存 ==========
def save_to_json(data):
    filename = "items.json" if data["type"] == "record" else "schedules.json"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            records = json.load(f)
    except FileNotFoundError:
        records = []
    records.append(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"✅ 資料已儲存至 {filename}")

# ========== 功能分類 ==========
def check_intent_with_gemini(text):
    prompt = f"""你是一個語意分類助手，請判斷這句話是否是在「記錄物品的位置」。\n句子：「{text}」\n請只回答：\nA（如果是在記錄物品放置）\nB（如果是聊天、敘述、非記錄）"""
    return safe_generate(prompt) or "B"

def check_schedule_intent_with_gemini(text):
    prompt = f"""你是一個語意分類助手，請判斷這句話是否是在「安排時程」。\n句子：「{text}」\n請只回答：\nA（如果是在安排時程）\nB（如果是聊天、記錄物品、其他非時程安排的語句）"""
    return safe_generate(prompt) or "B"

# ========== 擷取內容 ==========
def extract_item_info_with_gemini(text):
    prompt = f"""請從下面這句話中擷取出下列資訊，並用 JSON 格式回覆：\n- item：物品名稱\n- location：放置位置\n- owner：誰的（如果句中沒提到請填「我」）\n句子：「{text}」\n回傳格式：\n{{"item": "...", "location": "...", "owner": "..."}}"""
    reply = safe_generate(prompt)
    if reply and reply.startswith("```"):
        reply = reply.strip("`").replace("json", "").strip()
    try:
        data = json.loads(reply)
        return data.get("item"), data.get("location"), data.get("owner")
    except:
        return None, None, None

def extract_place_with_gemini(location_text):
    prompt = f"""請從下面這段描述中推測其所屬的「地點分類」，如：客廳、廚房、臥室等。\n描述：「{location_text}」\n請只回傳分類，不加解釋。"""
    return safe_generate(prompt) or "未知"

def extract_schedule_info_with_gemini(text):
    prompt = f"""請從這句話擷取下列資訊，用 JSON 回覆：\n- task：做什麼\n- location：地點描述\n- place：地點分類（如客廳、學校）\n- time：時間\n- person：誰（若未提及填「我」）\n句子：「{text}」\n格式：\n{{"task": "...", "location": "...", "place": "...", "time": "...", "person": "..."}}"""
    reply = safe_generate(prompt)
    if reply and reply.startswith("```"):
        reply = reply.strip("`").replace("json", "").strip()
    try:
        data = json.loads(reply)
        return data["task"], data["location"], data["place"], data["time"], data["person"]
    except:
        return None, None, None, None, None

# ========== 對話模式（有記憶） ==========
def chat_simulation(text):
    try:
        response = chat_session.send_message(text)
        save_chat_history(chat_session.history)  # 每次回應後儲存對話歷史
        return response.text.strip()
    except Exception as e:
        print("❌ Gemini 回應錯誤：", e)
        return "（系統暫時無法回應）"

# ========== 查詢功能 ==========
def query_items(keyword=None, today_only=False):
    try:
        with open("items.json", "r", encoding="utf-8") as f:
            records = json.load(f)
    except:
        print("❌ 尚無物品記錄。")
        return
    results = []
    for r in records:
        if today_only and not r["timestamp"].startswith(date.today().isoformat()):
            continue
        if keyword and keyword not in r["place"] and keyword not in r["location"]:
            continue
        results.append(r)
    if results:
        print(f"🔍 查到 {len(results)} 筆物品記錄：")
        for r in results:
            print(f" - [{r['timestamp']}] {r['owner']} 的「{r['item']}」放在 {r['location']}（{r['place']}）")
    else:
        print("❌ 查無結果。")

def query_schedules(keyword=None, today_only=False):
    try:
        with open("schedules.json", "r", encoding="utf-8") as f:
            records = json.load(f)
    except:
        print("❌ 尚無時程安排。")
        return
    results = []
    for r in records:
        if today_only and not r["timestamp"].startswith(date.today().isoformat()):
            continue
        if keyword and keyword not in r["task"] and keyword not in r["location"] and keyword not in r["place"]:
            continue
        results.append(r)
    if results:
        print(f"📅 查到 {len(results)} 筆時程安排：")
        for r in results:
            print(f" - [{r['timestamp']}] {r['person']} 在 {r['time']} 要「{r['task']}」地點：{r['location']}（{r['place']}）")
    else:
        print("❌ 查無結果。")

# ========== 主程式 ==========
def main():
    while True:
        text = input("請輸入一句話（輸入 q 離開）：")
        if text.lower() == "q":
            print("👋 再見！")
            break

        if text == "清除記憶":
            open(CHAT_HISTORY_FILE, "w", encoding="utf-8").write("[]")
            print("🧹 已清除 Gemini 記憶！")
            continue

        if text.startswith("查"):
            if "今天" in text and "安排" in text:
                query_schedules(today_only=True)
            elif "今天" in text and "物品" in text:
                query_items(today_only=True)
            elif "物品" in text:
                keyword = text.replace("查", "").replace("的物品", "").strip()
                query_items(keyword=keyword)
            elif "行程" in text or "安排" in text:
                keyword = text.replace("查", "").replace("的行程", "").replace("的安排", "").strip()
                query_schedules(keyword=keyword)
            else:
                print("❓ 無法辨識查詢指令，試試：查今天的安排 / 查廚房的物品")
            continue

        if check_intent_with_gemini(text) == "A":
            print("📦 判斷為物品記錄，擷取中...")
            item, location, owner = extract_item_info_with_gemini(text)
            if item and location:
                place = extract_place_with_gemini(location)
                print(f"✅ 擷取成功：物品「{item}」、位置「{location}」、地點「{place}」、擁有者「{owner}」")
                save_to_json({
                    "type": "record",
                    "item": item,
                    "location": location,
                    "place": place,
                    "owner": owner,
                    "raw_text": text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print("⚠️ 擷取失敗，請重試")

        elif check_schedule_intent_with_gemini(text) == "A":
            print("🗓 判斷為時程安排，擷取中...")
            task, location, place, time_info, person = extract_schedule_info_with_gemini(text)
            if task and location and time_info:
                print(f"📅 擷取成功：{person} 在 {time_info} 要「{task}」@{location}（{place}）")
                save_to_json({
                    "type": "schedule",
                    "task": task,
                    "location": location,
                    "place": place,
                    "time": time_info,
                    "person": person,
                    "raw_text": text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print("⚠️ 擷取失敗，請重試")

        else:
            reply = chat_simulation(text)
            print(f"💬 Gemini 回應：{reply}")

# ========== 執行 ==========
if __name__ == "__main__":
    main()
