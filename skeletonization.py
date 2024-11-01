import numpy as np


def B(p):
  # Count non-zero neighbors of p
  return np.sum(p)


def A(p):
  # Count transitions from 0 to 1 in the ordered sequence
  p.append(p[0])
  count = 0
  for i in range(len(p) - 1):
    if p[i] == 0 and p[i + 1] == 1:
      count += 1
  return count


def get_p(canvas, x, y):
  neighbors_indices = [
    (-1, 0), (-1, 1), (0, 1), (1, 1),
    (1, 0), (1, -1), (0, -1), (-1, -1)
  ]
  neighbors = []
  for di, dj in neighbors_indices:
    ni, nj = x + di, y + dj
    if 0 <= ni < canvas.shape[0] and 0 <= nj < canvas.shape[1]:
      neighbors.append(canvas[ni, nj])
    else:
      neighbors.append(0)  # Treat out-of-bounds pixels as background
  return neighbors


def hilditch_skeletonize(image, background_color, progress_bar=None):
  # Convert image to binary (0 and 1) format
  image = (image > 0).astype(int)
  if background_color:
    # Invert the array
    image = 1 - image
  change = True

  total_pixels = np.sum(image == 1)
  cumulative_removed_pixels = 0

  while change:
    change = False
    to_remove = np.zeros(image.shape, dtype=bool)

    # Iterate over each pixel, including borders
    for i in range(image.shape[0]):
      pixels_removed_in_iteration = 0
      for j in range(image.shape[1]):
        p1 = image[i, j]

        # Continue only if current pixel is black (1)
        if p1 == 1:
          # Get the 8 neighbors of the pixel, handling edges with `get_p`
          neighbors = get_p(image, i, j)

          b_p1 = B(neighbors)
          a_p1 = A(neighbors)

          # Apply Hilditch thinning conditions
          if (2 <= b_p1 <= 6 and
              a_p1 == 1 and
              (neighbors[0] * neighbors[2] * neighbors[6] == 0 or A(
                get_p(image, max(0, i - 1), j)) != 1) and
              (neighbors[0] * neighbors[2] * neighbors[4] == 0 or A(
                get_p(image, i, min(image.shape[1] - 1, j + 1))) != 1)):
            to_remove[i, j] = True
            pixels_removed_in_iteration += 1
            change = True

      cumulative_removed_pixels += pixels_removed_in_iteration

      # Update progress based on cumulative removed pixels
      if progress_bar and total_pixels > 0:
        progress_percentage = (cumulative_removed_pixels / total_pixels) * 100
        progress_bar["value"] = progress_percentage
        progress_bar.update_idletasks()

    # Remove pixels that met all conditions
    image[to_remove] = 0

  # Set progress bar to completed
  if progress_bar:
    progress_bar["value"] = 100
    progress_bar.update_idletasks()

  return image


def find_branch_and_end_points(skeleton):
  skeleton = (skeleton == 255).astype(int)
  rows, cols = skeleton.shape

  end_points = []
  branch_points = []

  for i in range(1, rows - 1):
    for j in range(1, cols - 1):
      if skeleton[i, j] == 1:
        neighbors = get_p(skeleton, i, j)

        count = np.sum(neighbors)

        transitions = A(neighbors + [neighbors[0]])

        if count == 1:
          end_points.append((i, j))
        elif count >= 3 and transitions >= 3:
          branch_points.append((i, j))

  return end_points, branch_points
