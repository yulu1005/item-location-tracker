import json
from ollama import chat

# 模型 A：使用 gemma3:1b 判斷語意（是否是記錄）
def check_intent_with_ollama(text):
    """判斷是否要記錄物品"""
    prompt = f"""
你是一個語句分類助手，請根據以下句子判斷使用者是否是在「記錄物品位置」。

句子：「{text}」

請只回答：
A（如果使用者是在說物品放在哪裡，要記錄）
B（如果不是記錄物品位置）

請只回答 A 或 B，不要加任何說明。
"""
    try:
        response = chat(model='gemma3:1b', messages=[{"role": "user", "content": prompt}])
        answer = response['message']['content'].strip()
        print("模型判斷回覆：", answer)
        return answer
    except Exception as e:
        print("❌ 呼叫 gemma3:1b發生錯誤：", e)
        return "B"

# 使用 LLM 擷取物品與放置位置（用 JSON 回傳）
def extract_item_info_with_llm(text):
    prompt = f"""
請從下面這句話中擷取出下列資訊，並用 JSON 格式回覆：

- item：物品名稱
- location：放置位置
- owner：物品是誰的（例如「我」、「媽媽」、「弟弟」等，若無明確指出請填「未知」）

句子：「{text}」

請回傳以下格式（勿加註解、標籤或 Markdown）：
{{
  "item": "...",
  "location": "...",
  "owner": "..."
}}
"""
    try:
        response = chat(model='gemma3:1b', messages=[{"role": "user", "content": prompt}])
        reply = response['message']['content'].strip()
        print("模型回覆 JSON：", reply)

        # 清除 markdown 格式（如 ```json ... ```)
        if reply.startswith("```"):
            reply = reply.strip("`").replace("json", "").strip()

        data = json.loads(reply)
        return data.get("item"), data.get("location"), data.get("owner")
    except Exception as e:
        print("❌ 擷取失敗：", e)
        return None, None, None

# 使用 LLM 判斷地點分類
def extract_place_with_ollama(location_text):
    prompt = f"""
請從下面這段描述中判斷對應的「地點分類」，例如：客廳、書房、廚房、臥室、浴室、門口、陽台、冰箱、衣櫃等。
如果無法判斷，請回答：未知。

描述：「{location_text}」

請只回答地點名稱，勿加說明。
"""
    try:
        response = chat(model='gemma3:1b', messages=[{"role": "user", "content": prompt}])
        place = response['message']['content'].strip()
        print("模型判斷地點：", place)
        return place
    except Exception as e:
        print("❌ 呼叫地點分類出錯：", e)
        return "未知"

# 模型 B：聊天回應（如果不是記錄）
def chat_with_elderly_bot(text):
    try:
        response = chat(model='gemma3_elderly', messages=[{"role": "user", "content": text}])
        reply = response['message']['content'].strip()
        return reply
    except Exception as e:
        return f"⚠️ 聊天出錯：{e}"

# 主程式
def main():
    while True:
        text = input("請輸入一句話（輸入 q 離開）：")

        if text.lower() == 'q':
            print("結束測試。")
            break

        intent = check_intent_with_ollama(text)

        if "A" in intent:
            print("🟢 模型判斷為記錄語句，開始擷取...")
            item, location = extract_item_location_with_llm(text)
            if item and location:
                place = extract_place_with_ollama(location)
                print(f"✅ 擷取成功！物品「{item}」、位置「{location}」、地點「{place}」")
            else:
                print("⚠️ 擷取失敗，請確認句子內容是否清楚")
        else:
            print("🟡 模型判斷為聊天，進行回應...")
            reply = chat_with_elderly_bot(text)
            print(f"🤖 聊天機器人回應：{reply}")

if __name__ == "__main__":
    main()
