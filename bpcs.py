import numpy as np


start_marker = "~#@START_Marker#@~"
end_marker = "~#@END_Marker#@~"
def calculate_complexity(block):
    """
    Calcule la complexité d’un bloc binaire (8x8 typiquement).
    Complexité = (nombre de changements de bits adjacents) / (nombre maximal possible).
    """
    height, width = block.shape
    total_changes = 0

    # Horizontal changes
    for i in range(height):
        total_changes += np.sum(block[i, :-1] != block[i, 1:])

    # Vertical changes
    for j in range(width):
        total_changes += np.sum(block[:-1, j] != block[1:, j])

    max_changes = 2 * (height * (width - 1))
    return total_changes / max_changes


def conjugate_block(block):
    """
    Conjugue un bloc (inversion XOR avec un damier) pour augmenter sa complexité.
    """
    checkerboard = np.indices(block.shape).sum(axis=0) % 2
    return block ^ checkerboard


def is_complex(block, threshold=0.3):
    """
    Vérifie si un bloc est suffisamment complexe selon un seuil.
    """
    return calculate_complexity(block) >= threshold


def to_bit_planes(image):
    """
    Transforme une image en plans binaires (8 bits par pixel, par canal).
    Retour : tableau [H, W, 8] de bits
    """
    bit_planes = np.unpackbits(image[:, :, np.newaxis], axis=2, bitorder='big')
    return bit_planes.reshape(*image.shape, 8)


def from_bit_planes(bit_planes):
    """
    Recompose une image à partir de ses plans binaires.
    """
    bits = bit_planes.reshape(*bit_planes.shape[:2], -1)
    image = np.packbits(bits, axis=2, bitorder='big')
    return image[:, :, 0]


def embed_block_into_plane(plane, block, x, y):
    """
    Insère un bloc binaire dans un plan binaire à la position (x, y).
    """
    h, w = block.shape
    plane[y:y+h, x:x+w] = block
    return plane


def extract_block_from_plane(plane, x, y, size=8):
    """
    Extrait un bloc binaire depuis un plan à la position (x, y).
    """
    return plane[y:y+size, x:x+size]

def deconjugate_block(block):
    """
    Applique la déconjugaison (inverse de la conjugaison).
    Ici c'est la même opération XOR avec le même motif.
    """
    # motif damier 8x8 identique
    pattern = np.fromfunction(lambda i, j: (i + j) % 2, block.shape, dtype=int)
    return np.bitwise_xor(block, pattern)