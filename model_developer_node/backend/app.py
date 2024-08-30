import os
import sys

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import requests
from utils import encrypt_data, decrypt_data
import json
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'bin', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_OWNER_URL = 'http://localhost:5001'
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', b'your-encryption-key-here')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_model', methods=['POST'])
def upload_model():
    uploaded_files = []
    for file_type in ['config', 'model', 'tokenizer_config', 'vocab', 'merges']:
        if file_type not in request.files:
            return jsonify({"error": f"Missing {file_type} file"}), 400
        file = request.files[file_type]
        if file.filename == '':
            return jsonify({"error": f"No selected file for {file_type}"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            uploaded_files.append(filename)
        else:
            return jsonify({"error": f"Invalid file type for {file_type}"}), 400
    return jsonify({"message": "Model files uploaded successfully", "uploaded_files": uploaded_files}), 200

@app.route('/initiate_evaluation', methods=['POST'])
def initiate_evaluation():
    model_files = request.json.get('model_files')
    if not model_files:
        return jsonify({"error": "No model files specified"}), 400

    evaluation_id = str(uuid.uuid4())
    model_data = {}
    for filename in model_files:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({"error": f"Model file not found: {filename}"}), 404
        with open(filepath, 'rb') as file:
            model_data[filename] = file.read()

    encrypted_model = encrypt_data(model_data, ENCRYPTION_KEY)
    response = requests.post(f"{DATA_OWNER_URL}/receive_model", 
                             data=encrypted_model,
                             headers={'Evaluation-ID': evaluation_id})
    if response.status_code == 200:
        return jsonify({"message": "Evaluation initiated", "evaluation_id": evaluation_id}), 200
    else:
        return jsonify({"error": "Failed to send model to Data Owner Node"}), 500

@app.route('/receive_results', methods=['POST'])
def receive_results():
    encrypted_results = request.data
    evaluation_id = request.headers.get('Evaluation-ID')
    decrypted_results = decrypt_data(encrypted_results, ENCRYPTION_KEY)
    
    # Store results (in a real application, you'd use a database)
    with open(f'results_{evaluation_id}.json', 'w') as f:
        json.dump(decrypted_results, f)
    
    return jsonify({"message": "Results received and processed"}), 200

@app.route('/get_results/<evaluation_id>', methods=['GET'])
def get_results(evaluation_id):
    try:
        with open(f'results_{evaluation_id}.json', 'r') as f:
            results = json.load(f)
        return jsonify(results), 200
    except FileNotFoundError:
        return jsonify({"error": "Results not found"}), 404

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)