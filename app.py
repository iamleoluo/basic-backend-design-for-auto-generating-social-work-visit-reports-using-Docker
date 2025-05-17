from flask import Flask, jsonify, request
import subprocess
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/run', methods=['POST'])
def run_script():
    try:
        data = request.get_json()
        text = data.get('text', '')
        with open('input.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        result = subprocess.run([sys.executable, 'run.py'], capture_output=True, text=True, check=True)
        output = result.stdout + '\n' + result.stderr
        return jsonify({'output': output})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e), 'output': e.output + '\n' + e.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True) 