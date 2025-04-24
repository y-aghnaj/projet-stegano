import cv2
import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from extract import image_to_bitplanes, block_complexity, segment_blocks
import time

END_MARKER = "~END~"


def extract_bits_from_frame(frame_rgb: np.ndarray, threshold: float = 0.3) -> str:
    bits = ''
    channels = list(frame_rgb.transpose(2, 0, 1))
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for _, block in segment_blocks(planes[plane]):
                if block_complexity(block) >= threshold:
                    bits += ''.join(str(bit) for bit in block.flatten())
    return bits


def bits_to_bytes(bitstring: str) -> bytes:
    length = len(bitstring) - (len(bitstring) % 8)
    return bytes(int(bitstring[i:i + 8], 2) for i in range(0, length, 8))


def decrypt_and_find_message_with_markers(data: bytes, key: str) -> str | None:
    """Decrypt data, extract content between ~START~ and ~END~ markers."""
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes for AES.")
    if len(data) < 16:
        return None
    iv, ct = data[:16], data[16:]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    try:
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        txt = pt.decode('utf-8', errors='ignore')
        start = txt.find("~START~")
        end = txt.find("~END~")
        if start != -1 and end != -1 and end > start:
            return txt[start + 8:end]
    except Exception:
        pass
    return None


def decrypt_message(data: bytes, key: str) -> str | None:
    key_bytes = key.encode('utf-8')
    if len(data) < 16 or len(key_bytes) not in (16, 24, 32):
        return None
    iv, ciphertext = data[:16], data[16:]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    try:
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8', errors='ignore')
        if END_MARKER in plaintext:
            return plaintext.split(END_MARKER)[0]
    except Exception:
        return None
    return None


def extract_from_video(stego_video_path: str, key: str, frame_interval: int = 12) -> str:
    cap = cv2.VideoCapture(stego_video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video {stego_video_path}")
    else:
        print("[+] Successfully opened video file")

    frame_idx = 0
    step_counter = 0
    collected_bits = ""
    start_time = time.time()
    #max_duration = 1200

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            collected_bits += extract_bits_from_frame(rgb)
            step_counter += 1
            elapsed = time.time() - start_time
            print(f"[+] Message Extraction Run: {step_counter} | Time Elapsed: {elapsed:.1f}s")

            # Try to decrypt every step
            message = decrypt_and_find_message_with_markers(bits_to_bytes(collected_bits), key.encode('utf-8'))
            if message:
                cap.release()
                print("[+] Message extracted successfully.")
                return message

            # Every 20 steps, ask the user if they want to stop
            if step_counter % 20 == 0:
                try:
                    response = input("Do you wish to stop the extraction? [Y/n]: ").strip().lower()
                    if response == 'y':
                        print("[*] Extraction manually stopped by user.")
                        break
                except KeyboardInterrupt:
                    print("\n[*] Extraction interrupted by user.")
                    break

        frame_idx += 1

    cap.release()
    raise ValueError("Failed to extract hidden message. END_MARKER not found.")


if __name__ == '__main__':
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"

    extract_from_video("stegano_video.mp4", key)
