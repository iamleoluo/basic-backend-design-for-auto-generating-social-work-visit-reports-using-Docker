from typing import Optional, Dict, List
from prompt_core.chat import ChatBot
import json
import os

class PromptConfig:
    def __init__(self, default_model_id: str = None):
        self.default_model_id = default_model_id
    
    def set_default_model_id(self, model_id: str):
        self.default_model_id = model_id
    
    def get_default_model_id(self) -> Optional[str]:
        return self.default_model_id

class PromptManager:
    def __init__(self, default_model_id: str = None):
        """初始化 Prompt 管理器
        
        Args:
            default_model_id: 預設的 model id
        """
        self.config = PromptConfig(default_model_id)
        self.chat_bot = ChatBot(default_model_id=default_model_id)
        self.default_temperature = 0.0
        self.default_stream = False
        self.conversation_histories: Dict[str, List[Dict[str, str]]] = {}
        
    def set_default_model_id(self, model_id: str):
        self.config.set_default_model_id(model_id)
        self.chat_bot.set_model(model_id)
        
    def create_conversation(self, conversation_id: str) -> None:
        """建立新的對話歷史
        
        Args:
            conversation_id: 對話的唯一識別碼
        """
        if conversation_id not in self.conversation_histories:
            self.conversation_histories[conversation_id] = []
            
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """獲取特定對話的歷史記錄
        
        Args:
            conversation_id: 對話的唯一識別碼
            
        Returns:
            對話歷史列表
        """
        return self.conversation_histories.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str) -> None:
        """清除特定對話的歷史記錄
        
        Args:
            conversation_id: 對話的唯一識別碼
        """
        if conversation_id in self.conversation_histories:
            self.conversation_histories[conversation_id] = []
        
    def chat(self, 
            conversation_id: str,
            user_input: str,
            system_prompt: Optional[str] = None,
            temperature: Optional[float] = None,
            stream: Optional[bool] = None,
            model_id: Optional[str] = None) -> str:
        """使用特定的提示模板進行對話
        
        Args:
            conversation_id: 對話的唯一識別碼
            user_input: 用戶輸入的文本
            system_prompt: 系統提示詞
            temperature: 溫度參數
            stream: 是否使用流式輸出
            model_id: 指定的模型 id
        
        Returns:
            AI的回應文本
        """
        # 確保對話歷史存在
        self.create_conversation(conversation_id)
        
        # 準備消息列表
        messages = self.conversation_histories[conversation_id].copy()
        
        # 如果有系統提示詞且是新對話，添加到開頭
        if system_prompt and not messages:
            messages.insert(0, {"role": "system", "content": system_prompt})
        
        # 添加用戶輸入
        messages.append({"role": "user", "content": user_input})
        
        # 使用提供的參數或默認值
        temp = temperature if temperature is not None else self.default_temperature
        strm = stream if stream is not None else self.default_stream
        model_to_use = model_id if model_id is not None else self.config.get_default_model_id()
        
        # 進行對話
        response = self.chat_bot.chat(
            messages=messages,
            temperature=temp,
            stream=strm,
            model_id=model_to_use
        )
        
        # 更新對話歷史
        if system_prompt and not self.conversation_histories[conversation_id]:
            self.conversation_histories[conversation_id].append(
                {"role": "system", "content": system_prompt}
            )
        self.conversation_histories[conversation_id].append(
            {"role": "user", "content": user_input}
        )
        self.conversation_histories[conversation_id].append(
            {"role": "assistant", "content": response}
        )
        
        return response

    def set_default_parameters(self, temperature: float = 0.0, stream: bool = False) -> None:
        """設置默認參數
        
        Args:
            temperature: 默認溫度參數
            stream: 默認是否使用流式輸出
        """
        self.default_temperature = temperature
        self.default_stream = stream
        
    def delete_conversation(self, conversation_id: str) -> bool:
        """刪除特定對話的歷史記錄
        
        Args:
            conversation_id: 要刪除的對話ID
            
        Returns:
            bool: 是否成功刪除
        """
        return self.chat_bot.delete_conversation(conversation_id)

class PromptLibrary:
    """
    管理 prompt.json，提供查詢/列出 prompt 元件的功能
    """
    def __init__(self, prompt_json_path: str = "prompt.json"):
        self.prompt_json_path = prompt_json_path
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, dict]:
        if not os.path.exists(self.prompt_json_path):
            return {}
        with open(self.prompt_json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # 支援新版格式（dict + steps）
                if isinstance(data, dict) and "steps" in data:
                    data = data["steps"]
                if isinstance(data, list):
                    return {item['label']: item for item in data}
                else:
                    return {}
            except Exception as e:
                print(f"載入 prompt.json 失敗: {e}")
                return {}

    def get_prompt(self, label: str) -> Optional[dict]:
        prompt = self.prompts.get(label)
        if not prompt:
            return None
        # 若是 choice 類型，自動加明確指示
        if prompt.get('type') == 'choice':
            choices = prompt.get('choices', [])
            instruction = f"（請只回答以下選項之一：{', '.join(choices)}）"
            # 合併問題與指示
            prompt = prompt.copy()
            prompt['question'] = prompt['question'].strip() + instruction
        return prompt

    def list_prompts(self) -> List[dict]:
        return list(self.prompts.values())
