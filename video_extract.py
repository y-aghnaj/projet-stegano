import cv2
import numpy as np
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from extract import image_to_bitplanes, block_complexity, segment_blocks
import time

START_MARKER = "~|BPCS_START|~"
END_MARKER = "~|BPCS_END|~"


def extract_bits_from_frame(frame_rgb: np.ndarray, threshold: float = 0.3) -> str:
    bits = ''
    channels = list(frame_rgb.transpose(2, 0, 1))
    for c in range(3):
        planes = image_to_bitplanes(channels[c])
        for plane in range(4, 8):  # Only checking bitplanes 4-7
            for _, block in segment_blocks(planes[plane]):
                if block_complexity(block) >= threshold:
                    bits += ''.join(str(bit) for bit in block.flatten())
    return bits


def bits_to_bytes(bitstring: str) -> bytes:
    # Ensure bitstring length is a multiple of 8 (byte length)
    bitstring = bitstring + '0' * (8 - len(bitstring) % 8) if len(bitstring) % 8 != 0 else bitstring
    # Convert bitstring to bytes
    byte_length = len(bitstring) // 8  # Calculate how many bytes we have
    byte_array = bytearray(int(bitstring[i:i + 8], 2) for i in range(0, len(bitstring), 8))

    # Ensure the length of the byte array is a multiple of 16 bytes (AES block size)
    while len(byte_array) % 16 != 0:
        byte_array.append(0)  # Pad with zero bytes if needed

    return bytes(byte_array)


def decrypt_message_with_markers(data: bytes, key: str) -> str | None:
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
        start = txt.find(START_MARKER)
        end = txt.find(END_MARKER)
        if start != -1 and end != -1 and end > start:
            return txt[start + len(START_MARKER):end]  # Extract message between markers
    except Exception as e:
        print(f"Decryption error: {e}")
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

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # You can adjust this to capture all frames, or you can set a higher limit if needed.
        if frame_idx > 301:
            break

        if frame_idx % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            collected_bits += extract_bits_from_frame(rgb)
            step_counter += 1
            elapsed = time.time() - start_time
            print(f"[+] Message Extraction Run: {step_counter} | Frame: {frame_idx} | Time Elapsed: {elapsed:.1f}s")
            print(f"Collected bits so far: {len(collected_bits)}")

            # Ensure collected bits are properly padded before decryption
            padded_bits = bits_to_bytes(collected_bits)

            # Try to decrypt message with extracted bits
            message = decrypt_message_with_markers(padded_bits, key)
            if message:
                cap.release()
                print("[+] Message extracted successfully.")
                return message

            # Every 20 steps, check if user wants to stop extraction
            if step_counter % 20 == 0:
                try:
                    # Comment this line in production or leave it for debugging
                    response = 'n'  # For testing, we automatically don't stop
                    if response == 'y':
                        print("[*] Extraction manually stopped by user.")
                        break
                except KeyboardInterrupt:
                    print("\n[*] Extraction interrupted by user.")
                    break

        frame_idx += 1

    cap.release()
    print("[*] Extraction completed. No message found.")
    raise ValueError("Failed to extract hidden message. END_MARKER not found.")


if __name__ == '__main__':
    key = "59a4c722fb9d647d8ff9e5c1496a43d0"  # AES key for decryption

    # Adjust video file path to your actual file
    extract_from_video("stegano_video.mp4", key)
