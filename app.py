from flask import Flask, Response, request
import subprocess
import sys
import os
import tempfile
import uuid
import json
import time
import glob
import threading
import atexit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 創建臨時文件目錄來存放用戶會話文件
TEMP_DIR = os.path.join(os.getcwd(), 'temp_sessions')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# 🆕 並發控制
session_locks = {}  # 會話級別的鎖
locks_lock = threading.Lock()  # 保護 session_locks 字典的鎖

def get_session_lock(session_id: str) -> threading.Lock:
    """獲取會話專用的鎖"""
    with locks_lock:
        if session_id not in session_locks:
            session_locks[session_id] = threading.Lock()
        return session_locks[session_id]

# 🆕 定期清理任務
def cleanup_worker():
    """背景清理工作"""
    while True:
        try:
            cleanup_old_temp_configs()
            cleanup_old_session_files()
            time.sleep(300)  # 每5分鐘清理一次
        except Exception as e:
            print(f"⚠️ 清理工作出錯: {e}", file=sys.stderr)
            time.sleep(60)

# 啟動背景清理線程
cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
cleanup_thread.start()

# 程序退出時清理
atexit.register(lambda: cleanup_old_temp_configs())

def get_session_file_path(session_id: str, filename: str) -> str:
    """根據會話ID獲取文件路徑（保持向下相容）"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    return os.path.join(session_dir, filename)

def get_step_specific_file_path(session_id: str, step: str, file_type: str = 'input') -> str:
    """🆕 根據步驟和時間戳獲取唯一文件路徑，避免衝突"""
    timestamp = str(int(time.time() * 1000))  # 使用毫秒時間戳
    filename = f"{step}_{file_type}_{timestamp}.txt"
    
    session_dir = os.path.join(TEMP_DIR, session_id)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    file_path = os.path.join(session_dir, filename)
    print(f"📁 創建步驟文件: {file_path}", file=sys.stderr)
    return file_path

def get_concurrent_safe_file_path(session_id: str, operation: str) -> str:
    """🆕 獲取並發安全的文件路徑"""
    import threading
    thread_id = threading.get_ident()
    timestamp = str(int(time.time() * 1000))
    filename = f"{operation}_{thread_id}_{timestamp}.txt"
    
    session_dir = os.path.join(TEMP_DIR, session_id)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    return os.path.join(session_dir, filename)

def cleanup_session_files(session_id: str):
    """清理會話文件"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    if os.path.exists(session_dir):
        import shutil
        shutil.rmtree(session_dir)

def get_config_file_for_request(template: str, selected_sections: list = None, custom_settings: dict = None) -> str:
    """根據請求參數選擇或生成配置文件（向下相容）"""
    
    # 🛡️ 向下相容：如果沒有新參數，使用預設配置
    if selected_sections is None and not custom_settings:
        return get_default_config_for_template(template)
    
    # 🆕 新功能：根據選擇的段落動態生成配置
    base_config = get_default_config_for_template(template)
    
    if selected_sections:
        return generate_custom_config(base_config, selected_sections, custom_settings)
    
    return base_config

def get_default_config_for_template(template: str) -> str:
    """根據模板名稱獲取預設配置文件"""
    
    # 配置文件映射（向下相容現有模板）
    config_map = {
        '司法社工家庭訪視模板': 'run.json',
        '士林地院家事服務中心格式(ChatGPT)': 'run.json', 
        '士林地院家事服務中心格式(Claude)': 'run.json',
        '珍珠社會福利協會格式(ChatGPT)': 'run.json',
        '珍珠社會福利協會格式(Claude)': 'run.json'
    }
    
    config_file = config_map.get(template, 'run.json')
    
    # 確保配置文件存在
    if not os.path.exists(config_file):
        print(f"⚠️ 配置文件不存在: {config_file}，使用預設 run.json")
        return 'run.json'
    
    return config_file

def generate_custom_config(base_config_file: str, selected_sections: list, custom_settings: dict = None) -> str:
    """根據選擇的段落動態生成配置文件"""
    
    try:
        # 讀取基礎配置
        with open(base_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 🆕 實作段落選擇邏輯
        if selected_sections:
            print(f"📝 選擇的段落: {selected_sections}")
            custom_prompt = build_custom_prompt(selected_sections, custom_settings)
            
            # 修改配置中的 template
            if 'steps' in config and len(config['steps']) > 0:
                config['steps'][0]['template'] = custom_prompt
                print(f"🔧 已生成客製化Prompt，長度: {len(custom_prompt)} 字元")
        
        if custom_settings:
            print(f"⚙️ 自定義設定: {custom_settings}")
            # 根據風格偏好調整溫度參數
            if 'style' in custom_settings:
                config['temperature'] = get_temperature_for_style(custom_settings['style'])
        
        # 生成臨時配置文件
        temp_config_path = f"temp_config_{uuid.uuid4().hex[:8]}.json"
        with open(temp_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return temp_config_path
        
    except Exception as e:
        print(f"⚠️ 生成自定義配置失敗: {e}")
        return base_config_file

def build_custom_prompt(selected_sections: list, custom_settings: dict = None) -> str:
    """🆕 根據選擇的段落構建自定義Prompt"""
    
    try:
        # 讀取段落映射配置
        with open('section_mappings.json', 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        sections_data = mappings['sections']
        
        # 獲取模板基礎Prompt（這裡簡化處理，實際可以根據template參數選擇）
        base_prompt = "請你根據下面的逐字稿內容，幫我整理成結構化的家事商談報告。"
        
        # 構建段落指示
        section_instructions = []
        selected_section_data = []
        
        # 按優先級排序選擇的段落
        for section_key in selected_sections:
            if section_key in sections_data:
                selected_section_data.append((sections_data[section_key]['priority'], section_key, sections_data[section_key]))
        
        selected_section_data.sort(key=lambda x: x[0])  # 按優先級排序
        
        # 生成段落說明
        for priority, section_key, section_info in selected_section_data:
            section_instructions.append(section_info['prompt_template'])
        
        # 組合完整的Prompt
        full_prompt = f"""{base_prompt}

報告需要包含以下段落：

{chr(10).join(section_instructions)}

撰寫要求：
- 請根據逐字稿內容，進行必要的整合與重組，避免逐字複製
- 以客觀、清晰、社工報告常用的第三人稱文風撰寫  
- 若原文資訊不清楚，請合理推測但絕對要避免虛構
- 請確保每個段落內容充實且符合專業標準"""

        # 添加自定義設定
        if custom_settings:
            if 'notes' in custom_settings and custom_settings['notes'].strip():
                full_prompt += f"\n\n特殊要求：\n{custom_settings['notes']}"
            
            if 'style' in custom_settings:
                style_instruction = get_style_instruction(custom_settings['style'])
                full_prompt += f"\n\n報告風格：{style_instruction}"
        
        full_prompt += "\n\n以下是逐字稿：\n{input}"
        
        return full_prompt
        
    except Exception as e:
        print(f"⚠️ 構建自定義Prompt失敗: {e}")
        # 如果失敗，返回預設的Prompt
        return "請你根據下面的逐字稿內容，幫我整理成結構化的家事商談報告：\n\n{input}"

def get_temperature_for_style(style: str) -> float:
    """🆕 根據風格偏好獲取模型溫度參數"""
    style_temperatures = {
        'formal': 0.2,    # 正式風格，較低創造性
        'detailed': 0.4,  # 詳細分析，中等創造性  
        'concise': 0.3    # 簡潔風格，適中創造性
    }
    return style_temperatures.get(style, 0.3)

def get_style_instruction(style: str) -> str:
    """🆕 根據風格偏好獲取寫作指示"""
    style_instructions = {
        'formal': '請使用正式、客觀、專業的語調，條理清晰、邏輯嚴謹，採用第三人稱撰寫',
        'detailed': '請提供詳細、深入的分析，全面覆蓋各個層面，使用豐富的描述和專業術語',
        'concise': '請保持簡潔、重點突出，精簡有力地表達核心要點，言簡意賅'
    }
    return style_instructions.get(style, '請保持專業、客觀的寫作風格')

def cleanup_temp_config_if_needed(config_file: str):
    """清理臨時配置文件"""
    if config_file.startswith('temp_config_') and os.path.exists(config_file):
        try:
            os.remove(config_file)
            print(f"🗑️ 清理臨時配置: {config_file}")
        except Exception as e:
            print(f"⚠️ 清理配置文件失敗: {e}")

def cleanup_old_temp_configs():
    """定期清理舊的臨時配置文件"""
    for file in glob.glob("temp_config_*.json"):
        try:
            # 如果文件超過1小時，則刪除
            if time.time() - os.path.getctime(file) > 3600:
                os.remove(file)
                print(f"🗑️ 清理過期配置: {file}")
        except Exception as e:
            print(f"⚠️ 清理過期配置失敗: {e}")

def cleanup_old_session_files():
    """🆕 清理老舊會話文件"""
    try:
        current_time = time.time()
        
        for session_id in os.listdir(TEMP_DIR):
            session_dir = os.path.join(TEMP_DIR, session_id)
            if not os.path.isdir(session_dir):
                continue
                
            # 檢查會話目錄的最後修改時間
            if current_time - os.path.getmtime(session_dir) > 86400:  # 24小時
                try:
                    import shutil
                    shutil.rmtree(session_dir)
                    print(f"🗑️ 清理過期會話: {session_id}", file=sys.stderr)
                    
                    # 清理對應的會話鎖
                    with locks_lock:
                        if session_id in session_locks:
                            del session_locks[session_id]
                            
                except Exception as e:
                    print(f"⚠️ 清理會話失敗 {session_id}: {e}", file=sys.stderr)
                    
            else:
                # 清理會話內的老舊步驟文件
                cleanup_old_step_files(session_dir)
                
    except Exception as e:
        print(f"⚠️ 會話清理工作失敗: {e}", file=sys.stderr)

def cleanup_old_step_files(session_dir: str):
    """🆕 清理會話內老舊的步驟文件"""
    try:
        current_time = time.time()
        
        for filename in os.listdir(session_dir):
            file_path = os.path.join(session_dir, filename)
            
            # 只清理步驟文件（包含時間戳的文件）
            if '_' in filename and filename.endswith('.txt'):
                try:
                    # 如果文件超過2小時且不是最近的，則刪除
                    if current_time - os.path.getmtime(file_path) > 7200:
                        os.remove(file_path)
                        print(f"🗑️ 清理步驟文件: {file_path}", file=sys.stderr)
                except Exception as e:
                    print(f"⚠️ 清理步驟文件失敗 {file_path}: {e}", file=sys.stderr)
                    
    except Exception as e:
        print(f"⚠️ 步驟文件清理失敗: {e}", file=sys.stderr)

@app.route('/api/run', methods=['POST'])
def run_script():
    data = request.get_json()
    text = data.get('text', '')
    session_id = data.get('sessionId', str(uuid.uuid4()))  # 如果沒有提供 sessionId，生成一個新的
    
    def generate():
        # 🆕 使用步驟專用文件路徑，避免衝突
        input_file = get_step_specific_file_path(session_id, 'report', 'input')
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 修改 run.py 的調用，傳入會話ID和輸入文件路徑
        process = subprocess.Popen([
            sys.executable, 'run.py', 
            '--session-id', session_id,
            '--input-file', input_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        for line in process.stdout:
            yield line
        process.stdout.close()
        process.wait()
        
        # 清理臨時配置文件（如果是動態生成的）
        cleanup_temp_config_if_needed(config_file)
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/PersonGraph', methods=['POST'])
def run_person_graph():
    data = request.get_json()
    text = data.get('text', '')
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    def generate():
        print(f"收到人物關係圖請求，會話ID: {session_id}", file=sys.stderr)
        
        # 🆕 使用步驟專用文件路徑，避免衝突
        input_file = get_step_specific_file_path(session_id, 'person_graph', 'input')
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        process = subprocess.Popen([
            sys.executable, 'person_graph.py',
            '--session-id', session_id,
            '--input-file', input_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        for line in process.stdout:
            yield line
        process.stdout.close()
        process.wait()
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/PersonGraphChat', methods=['POST'])
def person_graph_chat():
    data = request.get_json()
    message = data.get('message', '')
    current_graph = data.get('currentGraph', '')
    transcript = data.get('transcript', '')  # 新增逐字稿
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    def generate():
        print(f"收到人物關係圖對話請求，會話ID: {session_id}", file=sys.stderr)
        print(f"用戶消息: {message}", file=sys.stderr)
        
        # 🆕 使用步驟專用文件路徑，避免衝突
        input_file = get_step_specific_file_path(session_id, 'person_graph_chat', 'input')
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(f"原始逐字稿:\n{transcript}\n\n當前人物關係圖JSON:\n{current_graph}\n\n用戶指令:\n{message}")
        
        process = subprocess.Popen([
            sys.executable, 'person_graph_chat.py',
            '--session-id', session_id,
            '--input-file', input_file,
            '--message', message,
            '--current-graph', current_graph or '{}',
            '--transcript', transcript
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        for line in process.stdout:
            yield line
        process.stdout.close()
        process.wait()
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/treatment-plan', methods=['POST'])
def generate_treatment_plan():
    """新增：處遇計畫生成API"""
    data = request.get_json()
    report_content = data.get('reportContent', '')
    main_issue = data.get('mainIssue', '')
    case_type = data.get('caseType', '')
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    def generate():
        print(f"🔄 生成處遇計畫，會話ID: {session_id}", file=sys.stderr)
        
        # 🆕 使用步驟專用文件路徑，避免與報告生成衝突
        input_file = get_step_specific_file_path(session_id, 'treatment', 'input')
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(f"報告內容:\n{report_content}\n\n主述議題:\n{main_issue}")
        
        # 使用處遇計畫配置（如果存在）
        treatment_config = 'treatment_plan.json' if os.path.exists('treatment_plan.json') else 'run.json'
        
        # 調用處遇計畫生成腳本
        process = subprocess.Popen([
            sys.executable, 'run.py',
            '--session-id', session_id,
            '--input-file', input_file,
            '--config-file', treatment_config
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        for line in process.stdout:
            yield line
            
        process.stdout.close()
        process.wait()
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id: str):
    """清理指定會話的文件"""
    try:
        cleanup_session_files(session_id)
        return {'status': 'success', 'message': f'會話 {session_id} 的文件已清理'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5353, debug=True) 
