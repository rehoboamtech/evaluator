import json
from cryptography.fernet import Fernet

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(json.dumps(data).encode())

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return json.loads(f.decrypt(encrypted_data).decode())