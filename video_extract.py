import cv2
import os
import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from hashlib import sha256
from embed import image_to_bitplanes, block_complexity, segment_blocks

START_MARKER = "~|BPCS_START|~"
END_MARKER = "~|BPCS_END|~"
FRAME_INTERVAL = 12
THRESHOLD = 0.3

def decrypt_message(ciphertext: bytes, key: str) -> str:
    key_bytes = sha256(key.encode()).digest()
    iv = ciphertext[:16]
    ct = ciphertext[16:]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size).decode()

def extract_bits_from_frame(frame_rgb, threshold=THRESHOLD):
    bits = ''
    channels = frame_rgb.transpose(2, 0, 1)
    for c in range(3):
        bitplanes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(bitplanes[plane]):
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    bits += ''.join(str(flat[k]) for k in range(8))
    return bits

def bits_to_bytes(bits: str) -> bytes:
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8) if len(bits[i:i+8]) == 8)

def extract_message_from_video(video_path, key):
    if not os.path.exists(video_path):
        raise FileNotFoundError("Video not found.")

    cap = cv2.VideoCapture(video_path)
    total_bits = ''
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % FRAME_INTERVAL == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            bits = extract_bits_from_frame(rgb)
            total_bits += bits
            print(f"[+] Frame {frame_idx} | Extracted {len(bits)} bits | Total: {len(total_bits)} bits")

        frame_idx += 1

    cap.release()

    try:
        data = bits_to_bytes(total_bits)
        decrypted = decrypt_message(data, key)
        print("[+] Decryption successful")
    except Exception as e:
        raise RuntimeError(f"[!] Decryption failed: {e}")

    if START_MARKER in decrypted and END_MARKER in decrypted:
        start = decrypted.find(START_MARKER) + len(START_MARKER)
        end = decrypted.find(END_MARKER)
        message = decrypted[start:end]
        print(f"[✓] Message extracted: {message}")
        with open("extracted_message.txt", "w", encoding="utf-8") as f:
            f.write(message)
    else:
        raise ValueError("[!] Markers not found in decrypted message")

if __name__ == "__main__":
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"  # AES key
    video_file = "stegano_video.mp4"

    try:
        extract_message_from_video(video_file, key)
    except Exception as e:
        print(f"\n[!] Extraction failed: {e}")
