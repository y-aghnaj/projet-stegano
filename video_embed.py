import cv2
import numpy as np
import os
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad
from extract import image_to_bitplanes, bitplanes_to_image, block_complexity, segment_blocks

START_MARKER = "~|BPCS_START|~"
END_MARKER = "~|BPCS_END|~"


def encrypt_message(message: str, key: str) -> bytes:
    message = START_MARKER + message + END_MARKER
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes.")
    iv = get_random_bytes(16)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
    return iv + encrypted


def bytes_to_bits(data: bytes) -> str:
    return ''.join(f'{byte:08b}' for byte in data)


def embed_bits_in_frame(frame_rgb: np.ndarray, bitstream: str, index: int, threshold=0.3) -> tuple[np.ndarray, int]:
    channels = list(frame_rgb.transpose(2, 0, 1))
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(planes[plane]):
                if index >= len(bitstream):
                    break
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    bits = bitstream[index:index + 8].ljust(8, '0')
                    for k in range(min(8, len(bits))):
                        flat[k] = int(bits[k])
                    planes[plane][i:i + 8, j:j + 8] = flat.reshape((8, 8))
                    index += 8
            channels[c] = bitplanes_to_image(planes)
    stego_frame = np.stack(channels).transpose(1, 2, 0)
    return stego_frame, index


def embed_in_video(input_video_path: str, output_video_path: str, key: str, message: str, frame_interval=12):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise RuntimeError("Failed to open input video.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    encrypted_data = encrypt_message(message, key)
    bitstream = bytes_to_bits(encrypted_data)
    print(f"[+] Total bits to embed: {len(bitstream)}")

    frame_idx = 0
    bit_index = 0
    embedded_frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0 and bit_index < len(bitstream):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stego_frame, bit_index = embed_bits_in_frame(rgb, bitstream, bit_index)
            bgr_stego = cv2.cvtColor(stego_frame, cv2.COLOR_RGB2BGR)
            out.write(bgr_stego)
            embedded_frame_count += 1
            print(f"[+] Embedded into frame {frame_idx} | Bits written: {bit_index}")
        else:
            out.write(frame)

        frame_idx += 1

    cap.release()
    out.release()

    if bit_index < len(bitstream):
        raise ValueError("Failed to embed entire message, video too short or too few complex blocks.")

    print(f"[✓] Embedding complete. {embedded_frame_count} frames used. Output saved to '{output_video_path}'")


if __name__ == "__main__":
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"
    message_file = "C://"

    if not os.path.exists(message_file):
        print(f"[!] {message_file} not found.")
    else:
        with open(message_file, "r", encoding="utf-8") as f:
            message = f.read().strip()
        if message:
            embed_in_video("input_video.mp4", "stegano_video.mp4", key, message)
        else:
            print("[!] input.txt is empty.")
