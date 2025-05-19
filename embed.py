from PIL import Image
import numpy as np
from video_utils import video_to_frames, frames_to_video
from bpcs_util import image_to_bitplanes, block_complexity,segment_blocks, bitplanes_to_image

# Embed secret data into an image using BPCS method
def embed_data_into_image(image_path, complexity_threshold=0.3):
    try:
        image = Image.open(image_path)
        mode = image.mode
        print(f"Image mode: {mode}")

        # Read secret message from file
        with open("input.txt", "r", encoding="utf-8") as f:
            secret_data = f.read().strip()

        if not secret_data:
            raise ValueError("input.txt is empty. Nothing to embed.")

        # Append end marker
        secret_data += "~END~"
        secret_bits = ''.join(format(ord(c), '08b') for c in secret_data)
        secret_index = 0

        # Convert image to channels depending on mode
        if mode == 'L':
            channels = [np.array(image)]
        elif mode == 'RGB':
            channels = list(np.array(image).transpose(2, 0, 1))
        else:
            raise ValueError("Only 'L' (grayscale) and 'RGB' images are supported.")

        # Iterate over channels and bit-planes to embed data
        for idx, channel in enumerate(channels):
            bitplanes = image_to_bitplanes(channel)
            for plane in range(4, 8):  # Use high bitplanes only
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

        # Check if all bits were embedded
        if secret_index < len(secret_bits):
            raise ValueError("Not enough complex blocks to embed full message.")

        # Merge channels back and save stego image
        if mode == 'RGB':
            stego_img = np.stack(channels).transpose(1, 2, 0)
        else:
            stego_img = channels[0]

        Image.fromarray(stego_img).save("stego_image.png")
        print("[+] Data embedded successfully into stego_image.png")

    except FileNotFoundError:
        print("[!] input.txt or image file not found.")
    except Exception as e:
        print(f"[!] Error during embedding: {e}")

# Embed data into the first frame of a video
def embed_data_into_video(video_path, complexity_threshold=0.3):
    frame_folder = "video_frames"
    frames = video_to_frames(video_path, frame_folder)
    if not frames:
        print("[!] No frames extracted from video.")
        return

    # Use only the first frame for embedding, since n-th frame breaks the code
    first_frame_path = frames[0]

    try:
        # Embed data into the first frame image file itself
        embed_data_into_image(first_frame_path, complexity_threshold)
    except Exception as e:
        print(f"[!] Embedding failed: {e}")
        return

    # Rebuild video from updated frames (first frame now modified)
    output_video_path = "stego_video.mp4" # Might want to make it into a variable.
    frames_to_video(frame_folder, output_video_path)

    print(f"[+] Data embedded into video and saved as {output_video_path}")

# Run embedding on default input video
if __name__ == "__main__":
    embed_data_into_video("input_video.mp4")
