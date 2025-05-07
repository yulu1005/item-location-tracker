## 🌟 Gemini 版本（使用 Google API）

本專案已整合 Google Gemini Pro 模型，用於判斷語意、提取物品資訊與行程安排，提升自然語言理解能力。

### 使用特點
- ✅ 自動判斷使用者輸入是否為記錄物品或安排行程
- ✨ 擷取物品名稱、位置、擁有者（若無則預設為「我」）
- 📌 將資料儲存為 JSON 格式（可搭配資料庫延伸）
- 💬 若非物品或行程語句，則轉為長輩風格的聊天模式

### 執行方式

```bash
pip install -r requirements.txt
export GOOGLE_API_KEY=你的金鑰
python main_gemini.py
