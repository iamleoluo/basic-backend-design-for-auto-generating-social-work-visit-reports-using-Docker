# 訪視報告自動生成後端（Docker 版）

本專案是一個彈性、可擴充的 Prompt Engineering 框架，支援多種 LLM（如 Ollama、OpenAI），可根據設定檔自動切換模型，並支援 per-step prompt 設計。所有對話流程、模型參數、輸入檔案皆可由設定檔（run.json、person_graph.json、setting.json）集中管理。

---

## 目錄結構

- `app.py`：Flask API 伺服器，負責接收前端請求並執行主流程。
- `run.py`：主流程控制，依據 `run.json` 執行多步驟對話。
- `person_graph.py`：人物關係圖流程腳本，依據 `person_graph.json` 執行 AI 抽取人物關係。
- `prompt_core/`：核心邏輯，包含 prompt 管理與 LLM API 封裝。
- `requirements.txt`：Python 依賴套件。
- `Dockerfile`：Docker 建置腳本。
- `run.json`、`person_graph.json`、`setting.json`：流程與模型設定檔。
- `input.txt`：暫存輸入檔案。

---

## 快速開始

1. 下載專案
   ```bash
   git clone https://github.com/iamleoluo/basic-backend-design-for-auto-generating-social-work-visit-reports-using-Docker.git
   cd <專案資料夾>
   ```
2. 編輯設定檔
   - `setting.json`：設定可用 LLM 模型與 API 金鑰。
   - `run.json`、`person_graph.json`：設定對話流程與每步 prompt。
3. 安裝依賴
   ```bash
   pip install -r requirements.txt
   ```
4. 啟動 Flask 伺服器
   ```bash
   python app.py
   ```
5. （可選）用 Docker 部署
   ```bash
   docker build -t visit-report-backend .
   docker run -e MY_OPENAI_KEY=sk-abc123456789 -p 5050:5050 visit-report-backend
   ```

---

## API 使用說明

- **POST** `/run`  
  - `body` 範例： `{ "text": "請貼上逐字稿內容..." }`
  - 回傳：流式 AI 報告內容
- **POST** `/PersonGraph`  
  - `body` 範例： `{ "text": "請貼上逐字稿內容..." }`
  - 回傳：流式 AI 產生的人物關係 JSON

---

## 設定檔範例

- `setting.json`：
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
- `run.json`、`person_graph.json`：請參考專案內範例，或根據需求自訂 prompt 與流程。

---

## 常見問題

- 請確認 `setting.json`、`run.json`、`person_graph.json` 格式正確。
- OpenAI 需填入有效 API key。
- 若需支援新平台，擴充 `prompt_core/chat.py` 的 ChatBot 類即可。
- 若用 Ollama，請確認模型已啟動且有 GPU 支援。

---

> 參考來源：[basic-backend-design-for-auto-generating-social-work-visit-reports-using-Docker](https://github.com/iamleoluo/basic-backend-design-for-auto-generating-social-work-visit-reports-using-Docker.git)
