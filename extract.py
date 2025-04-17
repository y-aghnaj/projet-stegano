from PIL import Image
import numpy as np


def image_to_bitplanes(img):
    bitplanes = []
    for i in range(8):
        bitplanes.append((img >> i) & 1)
    return np.array(bitplanes)


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


def embed_data_into_image(image_path, complexity_threshold=0.3):
    try:
        image = Image.open(image_path)
        mode = image.mode
        print(f"Image mode: {mode}")

        with open("input.txt", "r", encoding="utf-8") as f:
            secret_data = f.read().strip()

        if not secret_data:
            raise ValueError("input.txt is empty. Nothing to embed.")

        secret_data += "~END~"
        secret_bits = ''.join(format(ord(c), '08b') for c in secret_data)
        secret_index = 0

        if mode == 'L':
            channels = [np.array(image)]
        elif mode == 'RGB':
            channels = list(np.array(image).transpose(2, 0, 1))
        else:
            raise ValueError("Only 'L' (grayscale) and 'RGB' images are supported.")

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

        if secret_index < len(secret_bits):
            raise ValueError("Not enough complex blocks to embed full message.")

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


if __name__ == "__main__":
    embed_data_into_image("input.jpg")
