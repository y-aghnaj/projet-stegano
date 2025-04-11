from PIL import Image
import numpy as np

def image_to_bitplanes(img):
    """Split image into 8 bit-planes."""
    bitplanes = []
    for i in range(8):
        bitplanes.append((img >> i) & 1)
    return np.array(bitplanes)

def bitplanes_to_image(bitplanes):
    """Reconstruct image from bit-planes."""
    img = np.zeros(bitplanes[0].shape, dtype=np.uint8)
    for i in range(8):
        img += (bitplanes[i] << i)
    return img

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

def embed_data_into_image(image_path, secret_data, complexity_threshold=0.3):
    image = Image.open(image_path).convert('L')  # Grayscale
    img_np = np.array(image)
    bitplanes = image_to_bitplanes(img_np)

    secret_bits = ''.join(format(ord(c), '08b') for c in secret_data)
    secret_index = 0

    for plane in range(4, 8):  # Use higher bitplanes (4-7)
        for (i, j), block in segment_blocks(bitplanes[plane]):
            if secret_index >= len(secret_bits):
                break

            if block_complexity(block) >= complexity_threshold:
                # Embed one char (8 bits) in the block
                new_block = block.copy()
                bits = secret_bits[secret_index:secret_index + 8]
                if len(bits) < 8:
                    bits = bits.ljust(8, '0')
                flat = new_block.flatten()
                for k in range(8):
                    flat[k] = int(bits[k])
                bitplanes[plane][i:i+8, j:j+8] = flat.reshape((8, 8))
                secret_index += 8

    stego_img = bitplanes_to_image(bitplanes)
    stego_pil = Image.fromarray(stego_img)
    stego_pil.save("stego_image.png")
    print("[+] Data embedded and image saved as stego_image.png")
embed_data_into_image("9apw622a7oj71.jpg","Hello") #test image