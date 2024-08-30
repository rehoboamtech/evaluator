import json
from cryptography.fernet import Fernet
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted_data).decode())

def anonymize_results(results):
    # This is a simple anonymization technique
    # In a real-world scenario, you'd want to use more advanced techniques
    # such as differential privacy
    anonymized = {}
    for key, value in results.items():
        if isinstance(value, float):
            anonymized[key] = round(value, 2)
        else:
            anonymized[key] = value
    return anonymized

def calculate_metrics(predictions, ground_truth):
    return {
        "accuracy": accuracy_score(ground_truth, predictions),
        "precision": precision_score(ground_truth, predictions, average='weighted'),
        "recall": recall_score(ground_truth, predictions, average='weighted'),
        "f1_score": f1_score(ground_truth, predictions, average='weighted')
    }