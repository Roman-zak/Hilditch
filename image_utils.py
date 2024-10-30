import numpy as np
from PIL import Image


def binarize_image(image, threshold=128):
  """
  Converts a grayscale image to binary by setting pixels to either 0 or 255
  based on a threshold.

  Parameters:
  image (PIL.Image): A grayscale PIL image.
  threshold (int): The threshold value (0-255). Default is 128.

  Returns:
  PIL.Image: A binarized image with pixel values 0 or 255.
  """
  # Convert image to a numpy array
  pixels = np.array(image)

  # Apply threshold
  binary_pixels = np.where(pixels < threshold, 0, 255).astype(np.uint8)

  # Convert back to a PIL image
  binary_image = Image.fromarray(binary_pixels)

  return binary_image
