from prompt_core.prompt import PromptManager, PromptLibrary
import json
import sys
import argparse
import os

def main():
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='家庭關係圖對話處理腳本')
    parser.add_argument('--session-id', required=True, help='會話ID')
    parser.add_argument('--input-file', required=True, help='輸入文件路徑')
    parser.add_argument('--message', required=True, help='用戶消息')
    parser.add_argument('--current-graph', required=True, help='當前家庭關係圖JSON')
    parser.add_argument('--transcript', default='', help='原始逐字稿')
    parser.add_argument('--config-file', default='family_graph_chat.json', help='配置文件路徑')
    parser.add_argument('--graph-type', default='family', help='關係圖類型')
    
    args = parser.parse_args()
    
    # 檢查配置文件是否存在
    if not os.path.exists(args.config_file):
        print(f"錯誤：配置文件 {args.config_file} 不存在", file=sys.stderr)
        return

    with open(args.config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    default_model_id = config_data.get("default_model_id")
    
    pm = PromptManager(default_model_id=default_model_id)
    conversation_id = f"family_graph_chat_{args.session_id}"
    pm.create_conversation(conversation_id)

    print(f"開始處理家庭關係圖對話，會話 {args.session_id}", file=sys.stderr)
    print(f"用戶消息: {args.message}", file=sys.stderr)
    print(f"逐字稿長度: {len(args.transcript)} 字符", file=sys.stderr)

    # 從配置文件讀取模板
    steps = config_data.get("steps", [])
    if not steps:
        print("錯誤：配置文件中沒有找到步驟定義", file=sys.stderr)
        return
    
    # 使用配置文件中的模板
    step_config = steps[0]  # 取第一個步驟
    template = step_config.get("template", "")
    
    if not template:
        print("錯誤：配置文件中沒有找到模板", file=sys.stderr)
        return

    # 格式化提示詞
    formatted_prompt = template.format(
        input=f"原始逐字稿:\n{args.transcript}\n\n當前家庭關係圖JSON:\n{args.current_graph}\n\n用戶指令:\n{args.message}"
    )

    print("-----------------------------------------", file=sys.stderr)
    print(f"[家庭關係圖對話 {args.session_id}] 處理用戶指令", file=sys.stderr)
    
    response_content = ""
    json_started = False
    json_content = ""
    brace_count = 0
    
    for chunk in pm.chat(conversation_id, formatted_prompt, model_id=default_model_id, temperature=0.1, stream=True, as_generator=True):
        response_content += chunk
        
        # 檢查是否開始 JSON 部分
        if not json_started:
            if "[" in chunk:
                json_started = True
                # 找到第一個 [ 的位置
                start_pos = chunk.find("[")
                json_content = chunk[start_pos:]
                brace_count = json_content.count("[") - json_content.count("]")
            else:
                # 輸出回應內容
                print(json.dumps({"type": "response", "content": chunk}), flush=True)
        else:
            # 已經在 JSON 部分
            json_content += chunk
            brace_count += chunk.count("[") - chunk.count("]")
            
            # 如果方括號平衡，JSON 結束
            if brace_count == 0:
                # 清理 JSON 內容
                clean_json = json_content.strip()
                
                # 驗證 JSON 格式
                try:
                    parsed_json = json.loads(clean_json)
                    # 輸出清理後的 JSON
                    print(json.dumps({"type": "graph", "content": clean_json}), flush=True)
                except json.JSONDecodeError:
                    print(f"JSON 格式錯誤: {clean_json}", file=sys.stderr)
                
                json_started = False
                json_content = ""
                brace_count = 0

    print(f"\n家庭關係圖對話會話 {args.session_id} 處理完成", file=sys.stderr)
    print("-----------------------------------------", file=sys.stderr)

if __name__ == "__main__":
    main()