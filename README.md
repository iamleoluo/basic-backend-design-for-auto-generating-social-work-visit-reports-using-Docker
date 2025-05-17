# Visit Report Automation - Prompt Engineering 框架

## 功能簡介
本專案是一個彈性、可擴充的 Prompt Engineering 框架，支援多種 LLM（如 Ollama、OpenAI），可根據設定檔自動切換模型，並支援 per-step prompt 設計。所有對話流程、模型參數、輸入檔案皆可由設定檔（run.json、setting.json）集中管理，讓 prompt 工程與自動化流程更簡單、可維護。

---

## 技術架構

- **setting.json**：集中管理所有可用模型（如 Ollama、OpenAI），每個模型有唯一 id、平台、參數（如 url、api_key）。
- **run.json**：定義對話流程（steps）、預設模型 id、輸入檔案名稱。每個 step 可指定不同的模型與參數。
- **prompt_core/prompt.py**：負責對話歷史管理、參數傳導、與 ChatBot 溝通。
- **prompt_core/chat.py**：根據 model_id 自動切換 Ollama/OpenAI，並呼叫對應 API。
- **run.py**：主流程控制，僅負責讀取設定檔、執行對話流程，無需硬編碼任何參數。

---

## 設定與應用方式

### 1. 設定模型（setting.json）
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
    "api_key": "sk-xxx-your-openai-key"
  }
]
```

### 2. 設定對話流程（run.json）
```json
{
  "input_file": "input.txt",
  "default_model_id": "openai_gpt-4o",
  "steps": [
    {
      "label": "intro",
      "type": "chat",
      "template": "請根據以下內容開始回答：{input}",
      "model_id": "ollama_llama3.2"
    },
    {
      "label": "has_children",
      "type": "choice",
      "question": "個案有沒有孩子？",
      "choices": ["yes", "no"],
      "model_id": "ollama_llama3.2"
    },
    {
      "label": "children_names",
      "type": "text",
      "question": "請輸入所有孩子的名字，用逗號分隔。",
      "format": "name1,name2,name3",
      "model_id": "ollama_llama3.2"
    }
  ]
}
```
- `input_file`：指定輸入檔案名稱。
- `default_model_id`：全域預設模型。
- `steps`：每個步驟可指定不同的 prompt、模型、溫度等參數。

### 3. 主流程（run.py）
run.py 已極度精簡，所有參數皆由 run.json 控制：
```python
from prompt_core.prompt import PromptManager, PromptLibrary
import json

if __name__ == "__main__":
    with open("run.json", "r", encoding="utf-8") as f:
        run_data = json.load(f)

    input_file = run_data.get("input_file", "input.txt")
    default_model_id = run_data.get("default_model_id")
    steps = run_data.get("steps", [])

    prompt_lib = PromptLibrary("run.json")
    pm = PromptManager(default_model_id=default_model_id)
    conversation_id = "myconv"
    pm.create_conversation(conversation_id)

    with open(input_file, "r", encoding="utf-8") as f:
        input_text = f.read()

    for step in steps:
        label = step.get("label")
        model_id = step.get("model_id")
        temperature = step.get("temperature")
        prompt = prompt_lib.get_prompt(label)
        if not prompt:
            continue
        if "template" in prompt:
            q = prompt["template"].format(input=input_text)
        else:
            q = prompt.get("question", "")
        print(f"[Q] {q}")
        print(f"[AI] {pm.chat(conversation_id, q, model_id=model_id, temperature=temperature)}")

    print("=== 對話歷史 ===")
    for msg in pm.get_conversation_history(conversation_id):
        print(f"[{msg['role']}] {msg['content']}")

    pm.clear_conversation(conversation_id)
```

---

## 支援特點
- **多模型切換**：可於 run.json per-step 指定不同模型（如 openai/ollama）。
- **集中設定**：所有參數皆由設定檔管理，主程式無需硬編碼。
- **彈性擴充**：可輕鬆新增更多模型、平台、prompt 步驟。
- **對話歷史管理**：自動保存與清除對話歷史。

---

## 依賴安裝
```bash
pip install -r requirements.txt
```
- 需安裝 openai、ollama 等套件。

---

## 注意事項
- 請確保 setting.json、run.json 格式正確。
- openai 需填入有效 API key。
- 若有新平台，擴充 chat.py 的 ChatBot 類即可。

---

## 範例應用
1. 設定好 setting.json、run.json。
2. 準備 input.txt。
3. 執行：
```bash
python run.py
```
即可自動依照流程與模型設定完成多步驟對話。 