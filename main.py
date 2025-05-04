import json
from ollama import chat

# 模型 A：使用微調後的 Gemma 3.1B 模型進行意圖分類
def check_intent_with_ollama(text):
    prompt = f"""
你是一個語句分類助手，請根據以下句子判斷使用者是否是在「記錄物品位置」。

句子：「{text}」

請只回答：
A（如果使用者是在說物品放在哪裡，要記錄）
B（如果不是記錄物品位置）

請只回答 A 或 B，不要加任何說明。
"""
    try:
        response = chat(model='gemma3_intent:latest', messages=[{"role": "user", "content": prompt}])
        answer = response['message']['content'].strip()
        print("模型判斷回覆：", answer)
        return answer
    except Exception as e:
        print("錯誤：無法呼叫模型進行判斷：", e)
        return "B"

# 使用模型擷取物品資訊（item, location, owner）
def extract_item_info_with_llm(text):
    prompt = f"""
    請從下面這句話中擷取出下列資訊，並用 JSON 格式回覆：

    - item：物品名稱
    - location：放置位置
    - owner：物品是誰的（如果句中沒有明確提到擁有者，請填「我」代表使用者本人）

    句子：「{text}」

    請回傳以下格式（勿加註解、標籤或 Markdown）：
    {{
      "item": "...",
      "location": "...",
      "owner": "..."
    }}
    """
    try:
        response = chat(model='gemma3_intent:latest', messages=[{"role": "user", "content": prompt}])
        reply = response['message']['content'].strip()

        if reply.startswith("```"):
            reply = reply.strip("`").replace("json", "").strip()

        data = json.loads(reply)
        return data.get("item"), data.get("location"), data.get("owner")
    except Exception as e:
        print("錯誤：擷取失敗，格式錯誤或模型回應異常：", e)
        return None, None, None

# 使用模型擷取地點分類
def extract_place_with_ollama(location_text):
    prompt = f"""
請從下面這段描述中判斷對應的「地點分類」，例如：客廳、書房、廚房、臥室、浴室、門口、陽台、冰箱、衣櫃等。
如果無法判斷，請回答：未知。

描述：「{location_text}」

請只回答地點名稱，勿加說明。
"""
    try:
        response = chat(model='gemma3_intent:latest', messages=[{"role": "user", "content": prompt}])
        place = response['message']['content'].strip()
        print("模型判斷地點：", place)
        return place
    except Exception as e:
        print("錯誤：地點判斷失敗：", e)
        return "未知"

# 非記錄語句時，使用聊天模型應對
def chat_with_elderly_bot(text):
    try:
        response = chat(model='gemma3_elderly', messages=[{"role": "user", "content": text}])
        reply = response['message']['content'].strip()
        return reply
    except Exception as e:
        return f"聊天錯誤：{e}"

# 主程式
def main():
    while True:
        text = input("請輸入一句話（輸入 q 離開）：")

        if text.lower() == 'q':
            print("結束測試。")
            break

        intent = check_intent_with_ollama(text)

        if "A" in intent:
            print("模型判斷為記錄語句，開始擷取...")
            item, location, owner = extract_item_info_with_llm(text)
            if item and location:
                place = extract_place_with_ollama(location)
                print(f"擷取成功：物品「{item}」、位置「{location}」、地點「{place}」、擁有者「{owner}」")
            else:
                print("擷取失敗，請確認句子內容是否清楚")
        else:
            print("模型判斷為聊天，進行回應...")
            reply = chat_with_elderly_bot(text)
            print(f"聊天機器人回應：{reply}")

if __name__ == "__main__":
    main()
