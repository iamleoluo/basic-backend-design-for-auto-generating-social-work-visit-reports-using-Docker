from flask import Flask, Response, request
import subprocess
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/run', methods=['POST'])
def run_script():
    data = request.get_json()   # 這裡先取出
    text = data.get('text', '')
    def generate():
        with open('input.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        # 用 Popen 逐行讀 stdout
        process = subprocess.Popen([sys.executable, 'run.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            yield line
        process.stdout.close()
        process.wait()
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/PersonGraph', methods=['POST'])
def run_person_graph():
    data = request.get_json()
    text = data.get('text', '')
    def generate():
        print("收到請求，開始寫入 input.txt", file=sys.stderr)
        with open('input.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        process = subprocess.Popen([sys.executable, 'person_graph.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in process.stdout:
            yield line
        process.stdout.close()
        process.wait()
    return Response(generate(), mimetype='application/x-ndjson')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True) 