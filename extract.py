from PIL import Image
import numpy as np

def image_to_bitplanes(img):
    """Split image into 8 bit-planes."""
    bitplanes = []
    for i in range(8):
        bitplanes.append((img >> i) & 1)
    return np.array(bitplanes)

def block_complexity(block):
    """Calculate block complexity (edge changes)."""
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
    """Yield 8x8 blocks with their positions."""
    for i in range(0, bitplane.shape[0], block_size):
        for j in range(0, bitplane.shape[1], block_size):
            block = bitplane[i:i+block_size, j:j+block_size]
            if block.shape == (block_size, block_size):
                yield (i, j), block

def extract_data_from_image(stego_image_path, complexity_threshold=0.3):
    try:
        image = Image.open(stego_image_path).convert('L')
        img_np = np.array(image)
        bitplanes = image_to_bitplanes(img_np)

        secret_bits = ''
        for plane in range(4, 8):
            for (i, j), block in segment_blocks(bitplanes[plane]):
                if block_complexity(block) >= complexity_threshold:
                    flat = block.flatten()
                    bits = ''.join(str(flat[k]) for k in range(8))
                    secret_bits += bits

        # Convert bits to characters until ~END~
        secret_message = ''
        for i in range(0, len(secret_bits), 8):
            byte = secret_bits[i:i+8]
            if len(byte) == 8:
                char = chr(int(byte, 2))
                secret_message += char
                if secret_message.endswith("~END~"):
                    secret_message = secret_message[:-5]
                    break

        if "~END~" not in secret_message + "~END~":
            raise ValueError("End marker '~END~' not found. Message may be incomplete or corrupted.")

        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(secret_message)

        print("[+] Message extracted successfully into output.txt")

    except FileNotFoundError:
        print("[!] stego_image.png not found.")
    except Exception as e:
        print(f"[!] Error during extraction: {e}")


# Example usage
if __name__ == "__main__":
    extract_data_from_image("stego_image.png")
