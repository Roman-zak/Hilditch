# skeletonization.py
import numpy as np
import numpy as np
from skimage import morphology
from skimage.util import invert


def hilditch_skeletonize(image):
  # Define 8-neighborhood indices for clockwise sequence around p1
  neighbors_indices = [
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1)
  ]

  # Convert image to binary (0 and 1) format
  image = (image > 0).astype(int)
  change = True

  def B(p):
    # Count non-zero neighbors of p
    return np.sum(p)

  def A(p):
    # Count transitions from 0 to 1 in the ordered sequence
    count = 0
    for i in range(len(p) - 1):
      if p[i] == 0 and p[i + 1] == 1:
        count += 1
    return count

  while change:
    change = False
    to_remove = np.zeros(image.shape, dtype=bool)

    # Iterate over each pixel (excluding borders for simplicity)
    for i in range(1, image.shape[0] - 1):
      for j in range(1, image.shape[1] - 1):
        p1 = image[i, j]

        # Continue only if current pixel is black (1)
        if p1 == 1:
          # Get the 8 neighbors of the pixel
          neighbors = [image[i + di, j + dj] for di, dj in neighbors_indices]

          # Compute B(p1) and A(p1)
          b_p1 = B(neighbors)
          a_p1 = A(neighbors + [neighbors[0]])

          # Check Hilditch conditions
          if (2 <= b_p1 <= 6 and
              a_p1 == 1 and
              (neighbors[0] * neighbors[2] * neighbors[4] == 0 or A(
                neighbors[1:] + [neighbors[0]]) != 1) and
              (neighbors[0] * neighbors[2] * neighbors[6] == 0 or A(
                neighbors[3:] + neighbors[:3]) != 1)):
            to_remove[i, j] = True
            change = True

    # Remove pixels that met all conditions
    image[to_remove] = 0

  return image

def skeletonize(binary_image):
    """
    Skeletonizes a binary image using the Hilditch thinning algorithm.

    Parameters:
    binary_image (numpy.ndarray): A binary image where the foreground pixels are 1, and the background pixels are 0.

    Returns:
    numpy.ndarray: A binary image representing the skeleton.
    """
    # Ensure the binary image is inverted (foreground is 1, background is 0)
    binary_image = binary_image > 0  # Convert to boolean
    inverted_image = invert(binary_image)

    # Apply skeletonization using the Hilditch algorithm
    skeleton = morphology.skeletonize(inverted_image)

    # Convert back to uint8 (0 and 1 values) to match the input binary format
    skeleton = skeleton.astype(np.uint8)

    return skeleton