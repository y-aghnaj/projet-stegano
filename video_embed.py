import cv2
import os
import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad
from hashlib import sha256
from embed import image_to_bitplanes, block_complexity, segment_blocks

# Constants
START_MARKER = "~|BPCS_START|~"
END_MARKER = "~|BPCS_END|~"
MIN_CHUNK_SIZE = 1000  # in bits
FRAME_INTERVAL = 12
THRESHOLD = 0.3

def encrypt_message(message: str, key: str) -> bytes:
    key_bytes = sha256(key.encode()).digest()  # ensure 32-byte key
    cipher = AES.new(key_bytes, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
    return cipher.iv + ct_bytes

def bytes_to_bits(data: bytes) -> str:
    return ''.join(f'{byte:08b}' for byte in data)

def embed_bits_in_frame(frame_rgb, bitstream, threshold=THRESHOLD):
    embedded = 0
    idx = 0
    max_bits = len(bitstream)
    channels = frame_rgb.transpose(2, 0, 1)  # R, G, B

    for c in range(3):
        bitplanes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(bitplanes[plane]):
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    for k in range(8):
                        if idx < max_bits:
                            flat[k] = int(bitstream[idx])
                            idx += 1
                            embedded += 1
                        else:
                            break
                    bitplanes[plane][i:i+8, j:j+8] = flat.reshape((8, 8))
                if idx >= max_bits:
                    break
            if idx >= max_bits:
                break
        channels[c] = sum((bitplanes[b] << b for b in range(8)))
    frame_rgb = np.stack(channels, axis=0).transpose(1, 2, 0)
    return frame_rgb.astype(np.uint8), embedded

def embed_message_in_video(video_path, output_path, message, key):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width, height = int(cap.get(3)), int(cap.get(4))

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    encrypted = encrypt_message(START_MARKER + message + END_MARKER, key)
    bitstream = bytes_to_bits(encrypted)

    chunks = [bitstream[i:i+MIN_CHUNK_SIZE] for i in range(0, len(bitstream), MIN_CHUNK_SIZE)]
    print(f"[+] Encrypted message split into {len(chunks)} chunks of {MIN_CHUNK_SIZE} bits")

    chunk_idx = 0
    frame_idx = 0
    total_embedded = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if chunk_idx < len(chunks) and frame_idx % FRAME_INTERVAL == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            modified, bits_written = embed_bits_in_frame(rgb, chunks[chunk_idx])
            total_embedded += bits_written
            chunk_idx += 1
            print(f"[+] Frame {frame_idx} | Embedded chunk {chunk_idx}/{len(chunks)} ({bits_written} bits)")

            bgr = cv2.cvtColor(modified, cv2.COLOR_RGB2BGR)
            out.write(bgr)
        else:
            out.write(frame)

        frame_idx += 1

    cap.release()
    out.release()

    print(f"[✓] Finished embedding. Total bits embedded: {total_embedded}")
    print(f"[✓] Output saved to '{output_path}'")

if __name__ == "__main__":
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"  # AES 128/192/256 bit key (must match extraction)
    input_video = "C://stegano//test vid.mp4"
    output_video = "stegano_video.mp4"
    message_file = "C://stegano//Luther extract.txt"

    if not os.path.exists(message_file):
        print(f"[!] Error: message file '{message_file}' not found.")
    else:
        with open(message_file, "r", encoding="utf-8") as f:
            message = f.read().strip()
        if message:
            embed_message_in_video(input_video, output_video, message = message, key =key)
        else:
            print("[!] Error: input message file is empty.")


