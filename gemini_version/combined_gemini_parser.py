
import json
import time
from datetime import datetime, date
import google.generativeai as genai
import dateparser

# === 初始化 Gemini 模型 ===
genai.configure(api_key="AIzaSyBeQ39c5VUwOjOwtWijcZySCyt-hjVQyKY")  # ←請替換為你自己的金鑰
model = genai.GenerativeModel("gemini-2.0-flash")

# === 安全生成 ===
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

# === 中文時間翻譯英文 ===
def zh_to_en(text):
    mapping = {
        "下禮拜": "next week", "下星期": "next week",
        "這禮拜": "this week", "這星期": "this week",
        "禮拜": "week", "星期": "week",
        "一": "Monday", "二": "Tuesday", "三": "Wednesday",
        "四": "Thursday", "五": "Friday", "六": "Saturday",
        "日": "Sunday", "天": "Sunday",
        "今天": "today", "明天": "tomorrow", "後天": "day after tomorrow",
        "早上": "morning", "下午": "afternoon", "晚上": "evening"
    }
    for zh, en in mapping.items():
        text = text.replace(zh, f" {en} ")
    return text.strip()

# === 中文時間轉為具體日期 ===
def parse_time_to_date(text):
    translated = zh_to_en(text)
    dt = dateparser.parse(translated, settings={"PREFER_DATES_FROM": "future"})
    if dt:
        return dt.strftime("%Y-%m-%d")
    return None

# === 儲存資料 ===
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

# === 判斷意圖 ===
def check_intent_with_gemini(text):
    prompt = f"請判斷這句話是否是在「記錄物品的位置」。句子：「{text}」只回答 A 或 B"
    return safe_generate(prompt) or "B"

def check_schedule_intent_with_gemini(text):
    prompt = f"請判斷這句話是否是在「安排時程」。句子：「{text}」只回答 A 或 B"
    return safe_generate(prompt) or "B"

# === 擷取內容 ===
def extract_item_info_with_gemini(text):
    prompt = f'''請擷取下列句子的資訊：
{{
  "item": "...", "location": "...", "owner": "..."
}}
句子：「{text}」'''
    reply = safe_generate(prompt)
    if reply and reply.startswith("```"):
        reply = reply.strip("`").replace("json", "").strip()
    try:
        data = json.loads(reply)
        return data.get("item"), data.get("location"), data.get("owner")
    except:
        return None, None, None

def extract_place_with_gemini(location_text):
    prompt = f"請推測這個地點描述的分類：「{location_text}」"
    return safe_generate(prompt) or "未知"

def extract_schedule_info_with_gemini(text):
    prompt = f'''請擷取下列句子的資訊：
{{
  "task": "...", "location": "...", "place": "...", "time": "...", "person": "..."
}}
句子：「{text}」'''
    reply = safe_generate(prompt)
    if reply and reply.startswith("```"):
        reply = reply.strip("`").replace("json", "").strip()
    try:
        data = json.loads(reply)
        location = data.get("location") or data.get("place")
        return data["task"], location, data["place"], data["time"], data["person"]
    except:
        return None, None, None, None, None

# === 聊天回應 ===
def chat_simulation(text):
    return safe_generate(f"你是一個溫柔的陪伴型聊天助理，請自然回應：{text}") or "（系統暫時無法回應）"

# === 主程式 ===
def main():
    while True:
        text = input("請輸入一句話（輸入 q 離開）：")
        if text.lower() == "q":
            break

        if check_intent_with_gemini(text) == "A":
            item, location, owner = extract_item_info_with_gemini(text)
            if item and location:
                place = extract_place_with_gemini(location)
                print(f"📦 記錄物品：{item} 在 {location}（{place}），屬於 {owner}")
                save_to_json({
                    "type": "record",
                    "item": item, "location": location, "place": place,
                    "owner": owner, "raw_text": text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print("❌ 擷取失敗")

        elif check_schedule_intent_with_gemini(text) == "A":
            task, location, place, time_info, person = extract_schedule_info_with_gemini(text)
            if task and time_info:
                parsed_date = parse_time_to_date(time_info)
                print(f"📅 安排：{person} 在 {time_info}（→ {parsed_date}）要「{task}」@{location}（{place}）")
                save_to_json({
                    "type": "schedule",
                    "task": task, "location": location, "place": place,
                    "time": time_info, "parsed_date": parsed_date,
                    "person": person, "raw_text": text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                print("❌ 擷取失敗")
        else:
            print("💬 Gemini 回應：", chat_simulation(text))

if __name__ == "__main__":
    main()
