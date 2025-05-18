from PIL import Image
import numpy as np
from bpcs import (
    to_bit_planes, from_bit_planes,
    is_complex, conjugate_block,
    embed_block_into_plane,
    start_marker, end_marker
)


def segment_blocks(bitplane, block_size=8):
    for y in range(0, bitplane.shape[0], block_size):
        for x in range(0, bitplane.shape[1], block_size):
            block = bitplane[y:y + block_size, x:x + block_size]
            if block.shape == (block_size, block_size):
                yield (x, y), block


def embed_data_into_image(image_path, complexity_threshold=0.3):
    try:
        image = Image.open(image_path)
        mode = image.mode
        print(f"Image mode: {mode}")

        # Lecture du message secret
        with open("input.txt", "r", encoding="utf-8") as f:
            secret_data = f.read().strip()

        if not secret_data:
            raise ValueError("input.txt is empty. Nothing to embed.")

        # Ajout des marqueurs complexes autour du message
        secret_data = start_marker + secret_data + end_marker

        # Conversion en bits
        secret_bits = ''.join(format(ord(c), '08b') for c in secret_data)
        secret_index = 0

        # Extraction des canaux image
        if mode == 'L':
            channels = [np.array(image)]
        elif mode == 'RGB':
            channels = list(np.array(image).transpose(2, 0, 1))
        else:
            raise ValueError("Only 'L' and 'RGB' images supported.")

        for idx, channel in enumerate(channels):
            bitplanes = to_bit_planes(channel)
            for plane in range(4, 8):  # Plans LSB
                for (x, y), block in segment_blocks(bitplanes[:, :, plane]):
                    if secret_index >= len(secret_bits):
                        break
                    if is_complex(block, complexity_threshold):
                        bits = secret_bits[secret_index:secret_index + 8].ljust(8, '0')
                        bit_block = np.array([int(b) for b in bits], dtype=np.uint8).reshape((8, 1)).repeat(8, axis=1)
                        if not is_complex(bit_block, complexity_threshold):
                            bit_block = conjugate_block(bit_block)
                        bitplanes[:, :, plane] = embed_block_into_plane(bitplanes[:, :, plane], bit_block, x, y)
                        secret_index += 8
                if secret_index >= len(secret_bits):
                    break
            channels[idx] = from_bit_planes(bitplanes)

        if secret_index < len(secret_bits):
            raise ValueError("Not enough complex blocks to embed full message.")

        if mode == 'RGB':
            stego_img = np.stack(channels).transpose(1, 2, 0)
        else:
            stego_img = channels[0]

        Image.fromarray(stego_img).save("temp_stego_image.png")
        print("[+] Data embedded successfully into temp_stego_image.png")

    except FileNotFoundError:
        print("[!] input.txt or image file not found.")
    except Exception as e:
        print(f"[!] Error during embedding: {e}")


if __name__ == "__main__":
    embed_data_into_image("input.jpg")
