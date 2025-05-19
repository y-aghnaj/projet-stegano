import numpy as np

def image_to_bitplanes(img):
    bitplanes = []
    for i in range(8):
        bitplanes.append((img >> i) & 1)
    return np.array(bitplanes)
# Reconstruct image from its bit-planes
def bitplanes_to_image(bitplanes):
    img = np.zeros(bitplanes[0].shape, dtype=np.uint8)
    for i in range(8):
        img += (bitplanes[i] << i)
    return img
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