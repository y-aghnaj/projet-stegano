from PIL import Image
import numpy as np
import os
from video_utils import video_to_frames

# Converts an image array into its 8 bit-planes (from LSB to MSB)
def image_to_bitplanes(img):
    bitplanes = []
    for i in range(8):
        bitplanes.append((img >> i) & 1)
    return np.array(bitplanes)

# Calculates the complexity of an 8x8 block based on adjacent bit differences
def block_complexity(block):
    complexity = 0
    rows, cols = block.shape
    # Horizontal complexity
    for i in range(rows):
        for j in range(1, cols):
            complexity += block[i, j] != block[i, j - 1]
    # Vertical complexity
    for i in range(1, rows):
        for j in range(cols):
            complexity += block[i, j] != block[i - 1, j]
    max_complexity = 2 * (rows - 1) * cols
    return complexity / max_complexity

# Generator that yields 8x8 blocks from the bit-plane
def segment_blocks(bitplane, block_size=8):
    for i in range(0, bitplane.shape[0], block_size):
        for j in range(0, bitplane.shape[1], block_size):
            block = bitplane[i:i + block_size, j:j + block_size]
            if block.shape == (block_size, block_size):
                yield (i, j), block

# Extracts hidden message from a stego image
def extract_data_from_image(stego_image_path, complexity_threshold=0.3):
    try:
        image = Image.open(stego_image_path)
        mode = image.mode
        print(f"Image mode: {mode}")

        # Convert image to numpy arrays for processing based on mode
        if mode == 'L':
            channels = [np.array(image)]
        elif mode == 'RGB':
            channels = list(np.array(image).transpose(2, 0, 1))
        else:
            raise ValueError("Only 'L' (grayscale) and 'RGB' images are supported.")

        secret_bits = ''
        # Traverse each channel and extract bits from complex blocks in higher bit-planes
        for channel in channels:
            bitplanes = image_to_bitplanes(channel)
            for plane in range(4, 8):  # Use bit-planes 4 to 7
                for (i, j), block in segment_blocks(bitplanes[plane]):
                    if block_complexity(block) >= complexity_threshold:
                        flat = block.flatten()
                        bits = ''.join(str(flat[k]) for k in range(8))  # Read 8 bits from block
                        secret_bits += bits

        secret_message = ''
        # Convert collected bits into characters
        for i in range(0, len(secret_bits), 8):
            byte = secret_bits[i:i + 8]
            if len(byte) == 8:
                char = chr(int(byte, 2))
                secret_message += char
                if secret_message.endswith("~END~"):
                    secret_message = secret_message[:-5]  # Remove end marker
                    break

        # Check if message end marker was found
        if "~END~" not in secret_message + "~END~":
            raise ValueError("End marker '~END~' not found. Message may be incomplete or corrupted.")

        # Write extracted message to output.txt
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(secret_message)
            print(secret_message)

        print("[+] Message extracted successfully into output.txt")

    except FileNotFoundError:
        print("[!] stego_image.png not found.")
    except Exception as e:
        print(f"[!] Error during extraction: {e}")

# Extracts hidden data from the first frame of a video
def extract_data_from_video(video_path, complexity_threshold=0.3):
    frame_folder = "video_frames"
    #frames = video_to_frames(video_path, frame_folder)
    frames = sorted(
        [os.path.join(frame_folder, f) for f in os.listdir(frame_folder) if f.endswith(".png")]
    )
    if not frames:
        print("[!] No frames extracted from video.")
        return

    first_frame_path = "stego_image.png"
    extract_data_from_image("stego_image.png", complexity_threshold)

    print("[+] Data extracted from first frame of video.")

# Entry point for running extraction from stego video
if __name__ == "__main__":
    extract_data_from_image("stego_image.png")
