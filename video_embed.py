import cv2
import numpy as np
import os
from PIL import Image
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad
from embed import image_to_bitplanes, bitplanes_to_image, block_complexity, segment_blocks

END_MARKER = "~END~"

def encrypt_message(message: str, key: bytes) -> bytes:
    """AES-CBC encrypt the UTF-8 message + END_MARKER, return IV||ciphertext."""
    data = (message + END_MARKER).encode('utf-8')
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data, AES.block_size))
    return iv + ct

def fragment_bits(bitstr: str, bits_per_fragment: int = 512) -> list[str]:
    """Split a long bit-string into fragments of up to bits_per_fragment bits."""
    return [bitstr[i:i+bits_per_fragment] for i in range(0, len(bitstr), bits_per_fragment)]

def embed_chunk_into_frame(frame_rgb: np.ndarray, chunk_bits: str, threshold: float=0.3):
    """Embed chunk_bits (a string of '0'/'1') block by block into bitplanes."""
    channels = list(frame_rgb.transpose(2, 0, 1))  # R, G, B
    bit_idx = 0
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(planes[plane]):
                if bit_idx >= len(chunk_bits):
                    break
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    byte = chunk_bits[bit_idx:bit_idx+8].ljust(8, '0')
                    for k in range(8):
                        flat[k] = int(byte[k])
                    planes[plane][i:i+8, j:j+8] = flat.reshape(8,8)
                    bit_idx += 8
            if bit_idx >= len(chunk_bits):
                break
        channels[c] = bitplanes_to_image(planes)
        if bit_idx >= len(chunk_bits):
            break
    if bit_idx < len(chunk_bits):
        return None  # failed to embed whole chunk
    stego = np.stack(channels).transpose(1,2,0)
    return stego

def embed_into_video(
    video_path: str,
    output_path: str,
    secret_message: str,
    key: bytes,
    frame_interval: int = 12,
    bits_per_fragment: int = 512
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video {video_path!r}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)

    # pick codec based on extension
    ext = os.path.splitext(output_path)[1].lower()
    fourcc = cv2.VideoWriter_fourcc(*('mp4v' if ext in ('.mp4','.mov') else 'XVID'))
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # encrypt and fragment
    encrypted = encrypt_message(secret_message, key)
    bitstr = ''.join(f"{b:08b}" for b in encrypted)
    fragments = fragment_bits(bitstr, bits_per_fragment)

    total, embedded = len(fragments), 0
    frame_idx = 0

    print(f"[+] Embedding into {output_path}: {total} fragments, every {frame_interval}th frame")

    while True:
        ret, bgr = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0 and embedded < total:
            # convert to RGB for PIL
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            stego_rgb = embed_chunk_into_frame(rgb, fragments[embedded])
            if stego_rgb is not None:
                bgr = cv2.cvtColor(stego_rgb, cv2.COLOR_RGB2BGR)
                embedded += 1
                print(f"  • Fragment {embedded}/{total} embedded at frame {frame_idx}")
        out.write(bgr)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"[+] Done. Embedded {embedded}/{total} fragments.")
