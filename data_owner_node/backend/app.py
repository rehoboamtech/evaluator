from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from utils import decrypt_data, encrypt_data, anonymize_results, calculate_metrics
import requests
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from celery import Celery

app = Flask(__name__)
CORS(app)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

MODEL_FOLDER = 'received_models'
DATASET_FOLDER = 'datasets'
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', b'your-encryption-key-here')
MODEL_DEVELOPER_URL = 'http://localhost:5000'

@app.route('/receive_model', methods=['POST'])
def receive_model():
    encrypted_model = request.data
    evaluation_id = request.headers.get('Evaluation-ID')
    decrypted_model = decrypt_data(encrypted_model, ENCRYPTION_KEY)
    
    os.makedirs(MODEL_FOLDER, exist_ok=True)
    model_path = os.path.join(MODEL_FOLDER, f'received_model_{evaluation_id}.pt')
    torch.save(decrypted_model, model_path)
    
    # Trigger evaluation
    evaluate_model.delay(evaluation_id)
    
    return jsonify({"message": "Model received successfully and evaluation started"}), 200

@celery.task
def evaluate_model(evaluation_id):
    model_path = os.path.join(MODEL_FOLDER, f'received_model_{evaluation_id}.pt')
    dataset_path = os.path.join(DATASET_FOLDER, 'clinical_notes.json')
    
    if not os.path.exists(model_path) or not os.path.exists(dataset_path):
        return {"error": "Model or dataset not found"}
    
    # Load model and tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained("uf-ai/gatortron-base")
    
    # Load and preprocess dataset
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    
    predictions = []
    ground_truth = []
    
    for item in dataset:
        inputs = tokenizer(item['text'], return_tensors="pt", padding=True, truncation=True)
        outputs = model(**inputs)
        pred = torch.argmax(outputs.logits, dim=-1).item()
        predictions.append(pred)
        ground_truth.append(item['label'])
    
    metrics = calculate_metrics(predictions, ground_truth)
    anonymized_results = anonymize_results(metrics)
    
    # Send results back to Model Developer Node
    encrypted_results = encrypt_data(anonymized_results, ENCRYPTION_KEY)
    response = requests.post(f"{MODEL_DEVELOPER_URL}/receive_results", 
                             data=encrypted_results,
                             headers={'Evaluation-ID': evaluation_id})
    
    if response.status_code == 200:
        return {"message": "Evaluation completed and results sent"}
    else:
        return {"error": "Failed to send results to Model Developer Node"}

@app.route('/evaluation_status/<evaluation_id>', methods=['GET'])
def evaluation_status(evaluation_id):
    task = evaluate_model.AsyncResult(evaluation_id)
    if task.state == 'PENDING':
        return jsonify({"status": "In progress"}), 200
    elif task.state == 'SUCCESS':
        return jsonify({"status": "Completed"}), 200
    else:
        return jsonify({"status": "Failed", "error": str(task.result)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Changed port to 5002