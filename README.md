# 物品位置記錄功能 Item Location Tracker

本功能為資訊安慰類專題中的子機能，用於讓使用者可以用口說或打字，依靠 AI 自動辨識是否要記錄物品，擴充功能包括物品名稱、放置位置、擴充地點、物品擁有者。

---

##  技術使用

* **Ollama + Gemma3:1b**：用於辨識使用者是否有記錄意圖，以及分類地點 (ex: 客廳、書房)
* **Gemma3\_elderly**：貼心伴講式的聊天模型，應對非記錄意圖的內容
* **Python + JSON + 正則表示法**：獲 item / location / owner 資訊

---

## 功能流程

1. 使用者輸入一段自然語言

```
我把眼鏡放在書櫃第二層
```

2. 系統使用 `gemma3:1b` 進行 **語意分類**：

   * 如果是記錄類語句（A 類） → 進行擲獲
   * 否則為聊天類語句（B 類） → 依靠 `gemma3_elderly` 轉交給聊天模型較情較理

3. 若為記錄類：

   * 擲獲 `item`：眼鏡
   * 擲獲 `location`：書櫃第二層
   * 擲獲 `owner`：我
   * (可選) 分類 `place`：書房

---

## AI 語意分類器說明 (Binary Classifier)

本功能主要技術基礎為一個以 **標記字語範例為基礎的電腦學習分類器** (二元分類) ：

* 模型：`Gemma3:1b`，經過 LoRA 小量微調
* 資料：用 instruction-based JSON 格式編排而成
* 目的：以 prompt 讓模型單獨返回 A 或 B

---

## 執行方式

### 1. 安裝環境

如果有 `requirements.txt`：

```bash
pip install -r requirements.txt
```

如果沒有：

```bash
pip install ollama transformers datasets peft accelerate
```

---

### 2. 啟用模型 (2 個 terminal)

```bash
# Terminal A：分類 + 擲獲
ollama run gemma3:1b

# Terminal B：聊天模型
ollama run gemma3_elderly
```

---

### 3. 執行主程式

```bash
python record_item.py
```

---

## 輸出範例

```bash
物品：眼鏡
位置：書櫃第二層
擁有者：我
(地點分類：書房)
```

---

## 備註

* `record_item.py` 為主功能執行檔
* 如要自己微調分類模型，可使用 `train.py`
* 未來可搭配 GUI / App 進一步擴張
