import traceback
from PIL import Image
import numpy as np
from video_utils import video_to_frames
import re
from datetime import datetime
from tqdm import tqdm

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def image_to_bitplanes(img):
    return np.array([(img >> i) & 1 for i in range(8)])

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

def extract_text_from_image(image_path, complexity_threshold=0.3):
    image = Image.open(image_path)
    mode = image.mode
    if mode == 'L':
        channels = [np.array(image)]
    elif mode == 'RGB':
        channels = list(np.array(image).transpose(2, 0, 1))
    else:
        raise ValueError("Only 'L' and 'RGB' images are supported.")

    bits = ''
    for channel in channels:
        bitplanes = image_to_bitplanes(channel)
        for plane in range(4, 8):
            log(f"Processing bitplane {plane}")
            for position, block in segment_blocks(bitplanes[plane]):
                if block_complexity(block) >= complexity_threshold:
                    flat = block.flatten()
                    bits += ''.join(str(flat[k]) for k in range(8))

    chars = [chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8) if len(bits[i:i + 8]) == 8]
    return ''.join(chars)

def extract_data_from_image(stego_image_path, complexity_threshold=0.3):
    # GUI fallback to first frame of video
    extract_data_from_video(stego_image_path, complexity_threshold)

def extract_data_from_video(video_path, complexity_threshold=0.3):
    frame_folder = "extracted_frames"
    frames = video_to_frames(video_path, frame_folder)
    if not frames:
        log("No frames found.")
        return

    fragments = {}
    frame_indices = range(0, 24)

    #for frame_index in tqdm(frame_indices, desc="Extracting from frames"):
    for frame_index in frame_indices:
        try:
            raw_text = extract_text_from_image(frames[frame_index], complexity_threshold)
            log(f"[Frame {frame_index}] Raw extracted text preview: {repr(raw_text[:200])}")

            # More permissive regex:
            matches = re.findall(r"#(\d+):(.*?)(?=(#\d+:|~#END#~|$))", raw_text, re.DOTALL)
            print(matches)

            if not matches:
                log(f"[Frame {frame_index}] No valid chunks found in extracted text.")
                continue

            for idx_str, data in matches:
                idx = int(idx_str)
                print(idx)
                fragments[idx] = data
                log(f"Extracted chunk #{idx} from frame {frame_index}")
                if "~#END#~" in data:
                    log("End marker found in chunk.")
                    break

        except Exception as e:

            log(f"Failed to extract from frame {frame_index}: {e}")
            traceback.print_exc()

    if not fragments:
        raise ValueError("No valid message fragments found.")

    message = ''.join(fragments[i] for i in sorted(fragments))
    if "~#END#~" not in message:
        raise ValueError("End marker not found in extracted message.")

    message = message.replace("~#END#~", "")

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(message)

    log("[+] Message extracted successfully into output.txt")

if __name__ == "__main__":
    extract_data_from_video("stego_video.mp4")
