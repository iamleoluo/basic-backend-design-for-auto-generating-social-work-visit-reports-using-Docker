# 訪視報告自動生成後端（Docker 版）

本專案是一個彈性、可擴充的 Prompt Engineering 框架，支援多種 LLM（如 Ollama、OpenAI），可根據設定檔自動切換模型，並支援 per-step prompt 設計。所有對話流程、模型參數、輸入檔案皆可由設定檔（run.json、setting.json）集中管理。

---

## 目錄結構

- `app.py`：Flask API 伺服器，負責接收前端請求並執行主流程。
- `run.py`：主流程控制，依據 `run.json` 執行多步驟對話。
- `prompt_core/`：核心邏輯，包含 prompt 管理與 LLM API 封裝。
- `requirements.txt`：Python 依賴套件。
- `Dockerfile`：Docker 建置腳本。
- `run.json`、`setting.json`：流程與模型設定檔。
- `input.txt`：暫存輸入檔案。

---

## 快速開始

### 1. 下載專案

```bash
git clone https://github.com/iamleoluo/basic-backend-design-for-auto-generating-social-work-visit-reports-using-Docker.git
cd <專案資料夾>
```

### 2. 編輯設定檔

- `setting.json`：設定可用 LLM 模型與 API 金鑰。
- `run.json`：設定對話流程與每步 prompt。

### 3. Docker 建置與啟動

```bash
docker build -t visit-report-backend .
docker run -e MY_OPENAI_KEY=sk-abc123456789 -p 5050:5050 my_image_name
```

### 4. API 使用說明

- **POST** `http://127.0.0.1:5050/run`
  - `body` 範例：
    ```json
    { "text": "請貼上逐字稿內容..." }
    ```
  - 回傳：
    ```json
    { "output": "AI 產生的報告內容..." }
    ```

---

## 設定檔範例

### setting.json

```json
[
  {
    "id": "ollama_llama3.2",
    "platform": "ollama",
    "model": "llama3.2",
    "url": "http://127.0.0.1:11434"
  },
  {
    "id": "openai_gpt-4o",
    "platform": "openai",
    "model": "gpt-4o",
    "openai_api_key": "your_openai_key"
  }
]
```

### run.json

```json
{
  "input_file": "input.txt",
  "default_model_id": "openai_gpt-4o",
  "steps": [
    {
      "label": "intro",
      "type": "chat",
      "template": "你是一位專業家事社工，請根據以下逐字稿內容，協助我撰寫一份標準的社工紀錄報告。逐字稿如下：{input}"
    },
    {
      "label": "main_issue",
      "type": "text",
      "question": "請根據逐字稿內容撰寫【一、主述問題】段落..."
    }
    // ... 其餘步驟 ...
  ]
}
```

---

## 前端測試

可搭配 `flash_drive.html`，直接在瀏覽器貼上逐字稿，點擊按鈕呼叫 API，結果會顯示於畫面。

---

## 依賴

- Python 3.10+
- Flask
- openai
- flask-cors
- ollama

---

## 常見問題

- 請確認 `setting.json`、`run.json` 格式正確。
- OpenAI 需填入有效 API key。
- 若需支援新平台，擴充 `prompt_core/chat.py` 的 ChatBot 類即可。

---

如需更詳細的流程設計與擴充方式，請參考原始碼與註解。 
