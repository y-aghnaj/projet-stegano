from datetime import datetime
from PIL import Image
import numpy as np
from bpcs import (
    to_bit_planes, is_complex, deconjugate_block
)

def log_time(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def segment_blocks(bitplane, block_size=8):
    for y in range(0, bitplane.shape[0], block_size):
        for x in range(0, bitplane.shape[1], block_size):
            block = bitplane[y:y + block_size, x:x + block_size]
            if block.shape == (block_size, block_size):
                yield (x, y), block

def extract_data_from_image(stego_image_path, complexity_threshold=0.3):
    try:
        log_time("Starting extraction")
        image = Image.open(stego_image_path)
        mode = image.mode
        log_time(f"Image mode: {mode}")

        if mode == 'L':
            channels = [np.array(image)]
        elif mode == 'RGB':
            channels = list(np.array(image).transpose(2, 0, 1))
        else:
            raise ValueError("Only 'L' (grayscale) and 'RGB' images are supported.")

        secret_bits = ''
        block_counter = 0

        for channel_idx, channel in enumerate(channels):
            log_time(f"Processing channel {channel_idx}")
            bitplanes = to_bit_planes(channel)

            for plane in range(4, 8):
                log_time(f"Processing bitplane {plane}")
                for (x, y), block in segment_blocks(bitplanes[:, :, plane]):
                    block_counter += 1
                    if block_counter % 1000 == 0:
                        log_time(f"Processed {block_counter} blocks so far...")

                    if not is_complex(block, complexity_threshold):
                        block = deconjugate_block(block)

                    first_col = block[:, 0]
                    bits = ''.join(str(bit) for bit in first_col[:8])
                    secret_bits += bits

                    if len(secret_bits) >= 40:
                        temp_message = ''
                        for i in range(0, len(secret_bits), 8):
                            byte = secret_bits[i:i + 8]
                            if len(byte) < 8:
                                continue
                            temp_message += chr(int(byte, 2))

                        if "~END~" in temp_message:
                            secret_bits = secret_bits[:(temp_message.index("~END~") + 5) * 8]
                            log_time("End marker found, stopping extraction")
                            break
                else:
                    continue
                break

        log_time(f"Total blocks processed: {block_counter}")

        secret_message = ''
        for i in range(0, len(secret_bits), 8):
            byte = secret_bits[i:i + 8]
            if len(byte) < 8:
                continue
            secret_message += chr(int(byte, 2))
            if secret_message.endswith("~END~"):
                secret_message = secret_message[:-5]
                break

        if "~END~" not in secret_message + "~END~":
            raise ValueError("End marker '~END~' not found. Message may be incomplete or corrupted.")

        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(secret_message)
            log_time("Message extracted and saved to output.txt")
            print(secret_message)

        log_time("Extraction completed successfully")

    except FileNotFoundError:
        print("[!] stego_image.png not found.")
    except Exception as e:
        print(f"[!] Error during extraction: {e}")


if __name__ == "__main__":
    extract_data_from_image("temp_stego_image.png")
