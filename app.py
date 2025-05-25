from flask import Flask, Response, request
import subprocess
import sys
import os
import tempfile
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 創建臨時文件目錄來存放用戶會話文件
TEMP_DIR = os.path.join(os.getcwd(), 'temp_sessions')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def get_session_file_path(session_id: str, filename: str) -> str:
    """根據會話ID獲取文件路徑"""
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

@app.route('/run', methods=['POST'])
def run_script():
    data = request.get_json()
    text = data.get('text', '')
    session_id = data.get('sessionId', str(uuid.uuid4()))  # 如果沒有提供 sessionId，生成一個新的
    
    def generate():
        # 為每個會話創建獨立的輸入文件
        input_file = get_session_file_path(session_id, 'input.txt')
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
        
        # 可選：處理完成後清理文件（或保留一段時間）
        # cleanup_session_files(session_id)
    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/PersonGraph', methods=['POST'])
def run_person_graph():
    data = request.get_json()
    text = data.get('text', '')
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    def generate():
        print(f"收到人物關係圖請求，會話ID: {session_id}", file=sys.stderr)
        
        # 為每個會話創建獨立的輸入文件
        input_file = get_session_file_path(session_id, 'input.txt')
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

@app.route('/PersonGraphChat', methods=['POST'])
def person_graph_chat():
    data = request.get_json()
    message = data.get('message', '')
    current_graph = data.get('currentGraph', '')
    transcript = data.get('transcript', '')  # 新增逐字稿
    session_id = data.get('sessionId', str(uuid.uuid4()))
    
    def generate():
        print(f"收到人物關係圖對話請求，會話ID: {session_id}", file=sys.stderr)
        print(f"用戶消息: {message}", file=sys.stderr)
        
        # 創建包含完整上下文的輸入文件
        input_file = get_session_file_path(session_id, 'chat_input.txt')
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

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id: str):
    """清理指定會話的文件"""
    try:
        cleanup_session_files(session_id)
        return {'status': 'success', 'message': f'會話 {session_id} 的文件已清理'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True) 