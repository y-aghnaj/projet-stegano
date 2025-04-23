import cv2
import numpy as np
from PIL import Image
from extract import image_to_bitplanes, block_complexity, segment_blocks
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

END_MARKER = "~END~"

def extract_chunk_from_frame(frame_rgb: np.ndarray, threshold: float=0.3) -> str:
    """Read bits out of complex blocks in bitplanes 4–7 of each channel."""
    bits = ""
    channels = list(frame_rgb.transpose(2, 0, 1))
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (_, _), block in segment_blocks(planes[plane]):
                if block_complexity(block) >= threshold:
                    bits += "".join(str(b) for b in block.flatten())
    return bits

def bits_to_bytes(bitstr: str) -> bytes:
    # drop trailing bits so length is multiple of 8
    n = (len(bitstr)//8)*8
    return bytes(int(bitstr[i:i+8],2) for i in range(0,n,8))

def decrypt_and_find_message(data: bytes, key: bytes) -> str|None:
    """Try to decrypt data; return plaintext before END_MARKER or None."""
    if len(data) < 16:
        return None
    iv, ct = data[:16], data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    try:
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        txt = pt.decode('utf-8', errors='ignore')
        if END_MARKER in txt:
            return txt.split(END_MARKER)[0]
    except ValueError:
        pass
    return None

def extract_from_video(
    stego_video_path: str,
    key: bytes,
    frame_interval: int = 12
) -> str:
    cap = cv2.VideoCapture(stego_video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video {stego_video_path!r}")

    all_bits = ""
    frame_idx = 0
    print(f"[+] Extracting from {stego_video_path}, every {frame_interval}th frame")

    while True:
        ret, bgr = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            all_bits += extract_chunk_from_frame(rgb)
            # Try decryption
            data = bits_to_bytes(all_bits)
            msg = decrypt_and_find_message(data, key)
            if msg is not None:
                cap.release()
                print("[+] Message extracted!")
                return msg
        frame_idx += 1

    cap.release()
    raise ValueError("END_MARKER not found; extraction failed")
