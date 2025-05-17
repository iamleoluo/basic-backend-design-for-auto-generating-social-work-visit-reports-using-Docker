from ollama import Client
from typing import List, Dict, Optional, Union
import json
import os
import openai  # 新增

class ChatBot:
    def __init__(self, default_model_id: Optional[str] = None, setting_path: str = "setting.json"):
        """初始化聊天機器人
        
        Args:
            default_model_id: 預設的 model id
            setting_path: 設定檔路徑
        """
        self.setting_path = setting_path
        self.model_configs = self._load_settings()
        self.current_model_id = default_model_id
        self.model = None
        self.host = None
        self.client = None
        self.platform = None
        if default_model_id:
            self.set_model(default_model_id)

    def _load_settings(self):
        if not os.path.exists(self.setting_path):
            return {}
        with open(self.setting_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    configs = {item['id']: item for item in data}
                else:
                    return {}
            except Exception as e:
                print(f"載入 setting.json 失敗: {e}")
                return {}
        # 新增：讀取 api_key.json 並補齊 api_key
        api_key_path = os.path.join(os.path.dirname(self.setting_path), 'api_key.json')
        if os.path.exists(api_key_path):
            try:
                with open(api_key_path, 'r', encoding='utf-8') as f:
                    api_keys = json.load(f)
            except Exception as e:
                print(f"載入 api_key.json 失敗: {e}")
                api_keys = {}
        else:
            api_keys = {}
        for config in configs.values():
            # 若有 openai_api_key 欄位，則從 api_key.json 補上 api_key
            if 'openai_api_key' in config and not config.get('api_key'):
                key_name = config['openai_api_key']
                config['api_key'] = api_keys.get(key_name, '')
        return configs

    def set_model(self, model_id: str):
        self.current_model_id = model_id
        config = self.model_configs.get(model_id)
        if not config:
            raise ValueError(f"找不到 model_id: {model_id} 的設定")
        platform = config.get('platform')
        if platform == 'ollama':
            self.model = config.get('model')
            self.host = config.get('url')
            self.client = Client(host=self.host)
            self.platform = 'ollama'
        elif platform == 'openai':
            self.model = config.get('model')
            self.api_key = config.get('api_key')
            self.platform = 'openai'
        else:
            raise ValueError(f"不支援的平台: {platform}")

    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = 0.0, stream: bool = False, model_id: Optional[str] = None) -> str:
        """與AI進行對話
        
        Args:
            messages: 消息列表，包含對話歷史
            temperature: 溫度參數，控制回答的隨機性
            stream: 是否使用流式輸出
            model_id: 指定的模型 id（可選，若有則臨時切換）
            
        Returns:
            AI的回應文本
        """
        try:
            if model_id and model_id != self.current_model_id:
                self.set_model(model_id)
            if getattr(self, 'platform', None) == 'ollama':
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=stream,
                    options={"temperature": temperature}
                )
                if stream:
                    full_response = ""
                    for chunk in response:
                        if isinstance(chunk, dict) and 'message' in chunk:
                            content = chunk['message'].get('content', '')
                            if content:
                                full_response += content
                    response_text = full_response
                else:
                    response_text = response['message']['content']
                return response_text
            elif getattr(self, 'platform', None) == 'openai':
                openai.api_key = self.api_key
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=stream
                )
                if stream:
                    full_response = ""
                    for chunk in response:
                        if hasattr(chunk, 'choices') and chunk.choices:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                full_response += delta.content
                    response_text = full_response
                else:
                    response_text = response.choices[0].message.content
                return response_text
            else:
                return "不支援的平台"
        except Exception as e:
            error_message = f"發生錯誤: {str(e)}"
            return error_message
