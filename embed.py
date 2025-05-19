from PIL import Image
import numpy as np
from video_utils import video_to_frames, frames_to_video
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def image_to_bitplanes(img):
    return np.array([(img >> i) & 1 for i in range(8)])

def bitplanes_to_image(bitplanes):
    img = np.zeros(bitplanes[0].shape, dtype=np.uint8)
    for i in range(8):
        img += (bitplanes[i] << i)
    return img

def block_complexity(block):
    complexity = 0
    rows, cols = block.shape
    for i in range(rows):
        for j in range(1, cols):
            complexity += block[i, j] != block[i, j - 1]
    for i in range(1, rows):
        for j in range(cols):
            complexity += block[i, j] != block[i - 1, j]
    max_complexity = 2 * (rows - 1) * cols
    return complexity / max_complexity

def segment_blocks(bitplane, block_size=8):
    for i in range(0, bitplane.shape[0], block_size):
        for j in range(0, bitplane.shape[1], block_size):
            block = bitplane[i:i + block_size, j:j + block_size]
            if block.shape == (block_size, block_size):
                yield (i, j), block

def embed_text_in_image(image_path, text, output_path, complexity_threshold=0.3):
    image = Image.open(image_path)
    mode = image.mode
    if mode == 'L':
        channels = [np.array(image)]
    elif mode == 'RGB':
        channels = list(np.array(image).transpose(2, 0, 1))
    else:
        raise ValueError("Only 'L' and 'RGB' images are supported.")

    secret_bits = ''.join(format(ord(c), '08b') for c in text)
    secret_index = 0

    for idx, channel in enumerate(channels):
        bitplanes = image_to_bitplanes(channel)
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(bitplanes[plane]):
                if secret_index >= len(secret_bits):
                    break
                if block_complexity(block) >= complexity_threshold:
                    flat = block.flatten()
                    bits = secret_bits[secret_index:secret_index + 8].ljust(8, '0')
                    for k in range(8):
                        flat[k] = int(bits[k])
                    bitplanes[plane][i:i + 8, j:j + 8] = flat.reshape((8, 8))
                    secret_index += 8
            if secret_index >= len(secret_bits):
                break
        channels[idx] = bitplanes_to_image(bitplanes)

    if mode == 'RGB':
        stego_img = np.stack(channels).transpose(1, 2, 0)
    else:
        stego_img = channels[0]

    Image.fromarray(stego_img).save(output_path)
    return secret_index >= len(secret_bits)

def embed_data_into_image(image_path, complexity_threshold=0.3):
    # Used by GUI
    embed_data_into_video(image_path, complexity_threshold)

def embed_data_into_video(video_path, complexity_threshold=0.3):
    frame_folder = "video_frames"
    frames = video_to_frames(video_path, frame_folder)
    if not frames:
        log("No frames extracted from video.")
        return

    with open("input.txt", "r", encoding="utf-8") as f:
        full_message = f.read().strip()

    if not full_message:
        raise ValueError("input.txt is empty.")

    full_message += "~#END#~"

    # Fragment the message into ~512 char chunks
    chunk_size = 512
    fragments = [f"#{i}:{full_message[i:i + chunk_size]}" for i in range(0, len(full_message), chunk_size)]
    total_chunks = len(fragments)

    log(f"Embedding {len(full_message)} characters over {total_chunks} chunks...")

    success_count = 0
    for frame_index in range(0, len(frames), 12):
        if success_count >= total_chunks:
            break
        frame_path = frames[frame_index]
        output_path = frame_path  # overwrite
        fragment = fragments[success_count]
        success = embed_text_in_image(frame_path, fragment, output_path, complexity_threshold)
        if success:
            log(f"Embedded chunk #{success_count} into frame {frame_index}")
            success_count += 1
        else:
            log(f"Frame {frame_index} didn’t have enough complex blocks. Skipped.")

    if success_count < total_chunks:
        raise ValueError("Not enough capacity in video frames to embed full message.")

    output_video_path = "stego_video.mp4"
    frames_to_video(frame_folder, output_video_path)
    log(f"[+] Data embedded into video and saved as {output_video_path}")

if __name__ == "__main__":
    embed_data_into_video("input_video.mp4")

