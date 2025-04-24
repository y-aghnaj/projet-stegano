import cv2
import numpy as np
import os
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad
from embed import image_to_bitplanes, bitplanes_to_image, block_complexity, segment_blocks

START_MARKER = "~START~"
END_MARKER = "~END~"


def encrypt_message_with_markers(message: str, key: str) -> bytes:
    """AES-CBC encrypt the message with ~START~ and ~END~ markers."""
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes for AES.")
    marked = START_MARKER + message + END_MARKER
    data = marked.encode('utf-8')
    iv = os.urandom(16)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data, AES.block_size))
    return iv + ct


def encrypt_message(message: str, key: str) -> bytes:
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes for AES.")
    message_bytes = (message + END_MARKER).encode('utf-8')
    iv = os.urandom(16)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(message_bytes, AES.block_size))
    return iv + ciphertext


def message_to_bitstring(encrypted: bytes) -> str:
    return ''.join(f"{byte:08b}" for byte in encrypted)


def fragment_bits(bitstring: str, size: int = 512) -> list:
    return [bitstring[i:i + size] for i in range(0, len(bitstring), size)]


def embed_bits_into_frame(frame_rgb: np.ndarray, bits: str, threshold: float = 0.3) -> np.ndarray | None:
    channels = list(frame_rgb.transpose(2, 0, 1))
    bit_idx = 0
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(planes[plane]):
                if bit_idx >= len(bits):
                    break
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    byte_bits = bits[bit_idx:bit_idx + 8].ljust(8, '0')
                    for k in range(8):
                        flat[k] = int(byte_bits[k])
                    planes[plane][i:i + 8, j:j + 8] = flat.reshape((8, 8))
                    bit_idx += 8
            if bit_idx >= len(bits):
                break
        channels[c] = bitplanes_to_image(planes)
        if bit_idx >= len(bits):
            break
    return np.stack(channels).transpose(1, 2, 0) if bit_idx >= len(bits) else None


def embed_into_video(
        video_path: str,
        output_path: str,
        secret_message: str,
        key: str,
        frame_interval: int = 12,
        bits_per_chunk: int = 512
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    ext = os.path.splitext(output_path)[1].lower()
    fourcc = cv2.VideoWriter_fourcc(*('mp4v' if ext in ('.mp4', '.mov') else 'XVID'))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    encrypted = encrypt_message_with_markers(secret_message, key)
    bitstring = message_to_bitstring(encrypted)
    chunks = fragment_bits(bitstring, bits_per_chunk)

    print(f"[+] Embedding {len(chunks)} chunks, every {frame_interval}th frame")

    frame_idx = 0
    chunk_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if chunk_idx < len(chunks) and frame_idx % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            embedded_rgb = embed_bits_into_frame(rgb, chunks[chunk_idx])
            if embedded_rgb is not None:
                frame = cv2.cvtColor(embedded_rgb, cv2.COLOR_RGB2BGR)
                print(f"  • Embedded chunk {chunk_idx + 1}/{len(chunks)} at frame {frame_idx}")
                chunk_idx += 1

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    if chunk_idx < len(chunks):
        print(f"[!] WARNING: Only embedded {chunk_idx}/{len(chunks)} chunks.")
    else:
        print("[+] Embedding complete.")


if __name__ == "__main__":
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"
    inputpath = "C://stegano//test vid.mp4"
    output = "stegano_video.mp4"
    secret = "C://stegano//Luther extract.txt"
    embed_into_video(video_path=inputpath, output_path=output, secret_message=secret, key=key)
