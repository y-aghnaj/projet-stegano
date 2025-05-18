from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
import base64
import hashlib

def pad(text):
    pad_len = 16 - len(text) % 16
    return text + chr(pad_len) * pad_len

def unpad(text):
    pad_len = ord(text[-1])
    return text[:-pad_len]

def derive_key(password):
    return hashlib.sha256(password.encode()).digest()

def encrypt_message(message, password):
    key = derive_key(password)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(message).encode())
    return base64.b64encode(iv + encrypted).decode()

def decrypt_message(ciphertext, password):
    try:
        raw = base64.b64decode(ciphertext)
        key = derive_key(password)
        iv = raw[:16]
        encrypted = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted).decode()
        return unpad(decrypted)
    except Exception:
        raise ValueError("Decryption failed. Check the password or data integrity.")
def generate_key():
    key = get_random_bytes(32)  # 256-bit key
    return base64.b64encode(key).decode()
