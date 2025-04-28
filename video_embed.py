import os
import cv2
import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad
from embed import image_to_bitplanes, bitplanes_to_image, block_complexity, segment_blocks

# Constants
START_MARKER = "~|BPCS_START|~"
END_MARKER = "~|BPCS_END|~"

def encrypt_message(message: str, key: str) -> bytes:
    """Encrypt the message with AES-CBC and markers."""
    full_message = START_MARKER + message + END_MARKER
    key_bytes = key.encode('utf-8')
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError("Key must be 16, 24, or 32 bytes long.")
    iv = get_random_bytes(16)
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(full_message.encode('utf-8'), AES.block_size))
    return iv + encrypted

def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a bitstring."""
    return ''.join(f"{byte:08b}" for byte in data)

def fragment_bits(bitstring: str, bits_per_fragment: int = 512) -> list[str]:
    """Split bitstring into small fragments."""
    return [bitstring[i:i+bits_per_fragment] for i in range(0, len(bitstring), bits_per_fragment)]

def embed_chunk_into_frame(frame_rgb: np.ndarray, chunk_bits: str, threshold: float = 0.3) -> np.ndarray | None:
    """Embed one chunk of bits into a frame."""
    channels = list(frame_rgb.transpose(2, 0, 1))  # R, G, B
    bit_idx = 0
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):  # only high planes
            for (i, j), block in segment_blocks(planes[plane]):
                if bit_idx >= len(chunk_bits):
                    break
                if block_complexity(block) >= threshold:
                    flat = block.flatten()
                    byte = chunk_bits[bit_idx:bit_idx+8].ljust(8, '0')
                    for k in range(8):
                        flat[k] = int(byte[k])
                    planes[plane][i:i+8, j:j+8] = flat.reshape(8, 8)
                    bit_idx += 8
            if bit_idx >= len(chunk_bits):
                break
        channels[c] = bitplanes_to_image(planes)
        if bit_idx >= len(chunk_bits):
            break
    if bit_idx < len(chunk_bits):
        return None  # Not enough capacity
    stego = np.stack(channels).transpose(1, 2, 0)
    return stego

def embed_in_video(
    input_video_path: str,
    output_video_path: str,
    key: str,
    message: str,
    frame_interval: int = 12,
    bits_per_fragment: int = 512
):
    """Main function to embed a secret message into a video."""
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open input video: {input_video_path}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)

    ext = os.path.splitext(output_video_path)[1].lower()
    fourcc = cv2.VideoWriter_fourcc(*('mp4v' if ext in ('.mp4', '.mov') else 'XVID'))
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Encrypt and fragment message
    encrypted_data = encrypt_message(message, key)
    bitstream = bytes_to_bits(encrypted_data)
    fragments = fragment_bits(bitstream, bits_per_fragment)

    print(f"[+] Total fragments to embed: {len(fragments)}")

    frame_idx = 0
    fragment_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0 and fragment_idx < len(fragments):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            stego_rgb = embed_chunk_into_frame(rgb, fragments[fragment_idx])
            if stego_rgb is not None:
                bgr_stego = cv2.cvtColor(stego_rgb, cv2.COLOR_RGB2BGR)
                out.write(bgr_stego)
                print(f"[+] Fragment {fragment_idx + 1}/{len(fragments)} embedded at frame {frame_idx}")
                fragment_idx += 1
            else:
                print(f"[!] Warning: could not embed fragment {fragment_idx + 1} at frame {frame_idx} (complexity issue)")
                out.write(frame)  # Write original frame
        else:
            out.write(frame)

        frame_idx += 1

    cap.release()
    out.release()

    if fragment_idx < len(fragments):
        raise ValueError(f"Failed to embed all fragments! Embedded {fragment_idx}/{len(fragments)}.")

    print(f"[✓] Embedding complete: {fragment_idx}/{len(fragments)} fragments embedded into '{output_video_path}'.")

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
            embed_in_video(input_video, output_video, key, message)
        else:
            print("[!] Error: input message file is empty.")

if __name__ == "__main__":
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"
    key_bytes = key.encode('utf-8')
    message_file = "C://stegano//Luther extract.txt"
    input_video = "C://stegano//test vid.mp4"

    if not os.path.exists(message_file):
        print(f"[!] {message_file} not found.")
    else:
        with open(message_file, "r", encoding="utf-8") as f:
            message = f.read().strip()
        if message:
            embed_in_video(input_video, "stegano_video.mp4", key, message)
        else:
            print("[!] input.txt is empty.")
