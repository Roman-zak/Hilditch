import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image
from image_components import PanZoomCanvas
from image_utils import binarize_image
from skeletonization import hilditch_skeletonize, find_branch_and_end_points


class ImageSkeletonApp:
  def __init__(self, root):
    self.root = root
    self.root.title("Image Skeletonization App with Pan and Zoom")
    self.root.geometry("1200x800")

    # Background color option
    self.bg_color = tk.BooleanVar(value=0)  # Default to black

    # Upload and process buttons
    self.upload_button = tk.Button(root, text="Upload Image",
                                   command=self.upload_image)
    self.upload_button.pack(pady=10)

    self.process_button = tk.Button(root, text="Process Image",
                                    command=self.start_skeletonization_thread)
    self.process_button.pack(pady=10)
    self.process_button.config(state=tk.DISABLED)

    self.save_button = tk.Button(root, text="Save Processed Image",
                                 command=self.save_image)
    self.save_button.pack(pady=10)
    self.save_button.config(state=tk.DISABLED)

    # Background color selection
    self.bg_frame = tk.Frame(root)
    self.bg_frame.pack(pady=10)
    tk.Label(self.bg_frame, text="Choose Background Color:").pack(side=tk.LEFT)
    tk.Radiobutton(self.bg_frame, text="Black", variable=self.bg_color,
                   value=0).pack(side=tk.LEFT)
    tk.Radiobutton(self.bg_frame, text="White", variable=self.bg_color,
                   value=1).pack(side=tk.LEFT)

    # Intensity threshold slider
    self.threshold_label = tk.Label(root, text="Intensity Threshold:")
    self.threshold_label.pack()
    self.threshold_slider = tk.Scale(root, from_=0, to=255, orient="horizontal")
    self.threshold_slider.set(100)  # Default threshold
    self.threshold_slider.pack(pady=10)

    # Progress bar for skeletonization
    self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=300,
                                        mode="determinate")
    self.progress_bar.pack(pady=10)

    # Frame for side-by-side canvases
    self.canvas_frame = tk.Frame(root)
    self.canvas_frame.pack(pady=10, expand=True)

    # Original and Processed PanZoomCanvas placeholders
    self.original_canvas = PanZoomCanvas(self.canvas_frame)
    self.original_canvas.grid(row=0, column=0, padx=5, pady=5)
    self.processed_canvas = PanZoomCanvas(self.canvas_frame)
    self.processed_canvas.grid(row=0, column=1, padx=5, pady=5)

    self.processing_thread = None  # To track the skeletonization thread

  def upload_image(self):
    try:
      file_path = filedialog.askopenfilename(
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"),
                   ("BMP files", "*.bmp")]
      )
      if file_path:
        self.original_canvas.set_image(file_path)
        self.process_button.config(state=tk.NORMAL)
    except Exception as e:
      messagebox.showerror("File Open Error", f"An error occurred: {e}")

  def start_skeletonization_thread(self):
    """Start the skeletonization process in a separate thread."""
    self.process_button.config(state=tk.DISABLED)
    self.save_button.config(state=tk.DISABLED)
    self.progress_bar["value"] = 0  # Reset progress bar

    # Start skeletonization in a new thread
    self.processing_thread = threading.Thread(target=self.process_image)
    self.processing_thread.start()

    # Check thread status
    self.root.after(100, self.check_skeletonization_thread)

  def check_skeletonization_thread(self):
    """Check if the skeletonization thread is still running."""
    if self.processing_thread.is_alive():
      self.root.after(100, self.check_skeletonization_thread)
    else:
      # Enable save button after processing is complete
      self.save_button.config(state=tk.NORMAL)
      self.process_button.config(state=tk.NORMAL)

  def split_image_with_overlap(self, image_array, num_splits=4, padding=5):
    """Split the image into smaller chunks with overlap (padding) to avoid artifacts at boundaries."""
    h, w = image_array.shape
    split_height = h // num_splits
    chunks = []

    for i in range(num_splits):
      y_start = max(i * split_height - padding, 0)
      y_end = min((i + 1) * split_height + padding, h)
      chunk = image_array[y_start:y_end]
      chunks.append((chunk, y_start, y_end))

    return chunks

  def process_image_chunk(self, chunk, start, end, result_dict, idx):
    """Skeletonize a chunk of the image and store it in a result dictionary."""
    result_dict[idx] = hilditch_skeletonize(chunk, self.bg_color.get())

  def process_image(self):
    if self.original_canvas.pil_image:
      # Convert to grayscale and binarize
      image = self.original_canvas.pil_image
      gray_image = image.convert("L")
      threshold_value = self.threshold_slider.get()
      binary_image = np.array(
        binarize_image(gray_image, threshold_value)) // 255

      # Split image with padding for parallel processing
      chunks = self.split_image_with_overlap(binary_image)

      # Dictionary to collect results from each thread
      results = {}
      threads = []

      # Process each chunk in parallel
      for idx, (chunk, start, end) in enumerate(chunks):
        thread = threading.Thread(target=self.process_image_chunk,
                                  args=(chunk, start, end, results, idx))
        threads.append(thread)
        thread.start()

      # Wait for all threads to finish
      for thread in threads:
        thread.join()

      # Reassemble the processed chunks into a single skeletonized image
      skeleton = np.zeros_like(binary_image)
      for idx, (chunk, start, end) in enumerate(chunks):
        processed_chunk = results[idx]
        padding = 5 if idx != 0 and idx != len(
          chunks) - 1 else 0  # Remove padding for middle chunks
        skeleton[start + padding:end - padding] = processed_chunk[
                                                  padding:processed_chunk.shape[
                                                            0] - padding]

      # Find endpoints and branch points
      end_points, branch_points = find_branch_and_end_points(skeleton)

      # Convert the skeleton to RGB for colored marking
      colored_image = np.stack([skeleton * 255] * 3, axis=-1).astype(np.uint8)

      # Mark end points in blue and branch points in red
      for point in end_points:
        x, y = point[0], point[1]  # Unpack coordinates
        colored_image[x, y] = [0, 0, 255]  # Blue for endpoints

      for point in branch_points:
        x, y = point[0], point[1]  # Unpack coordinates
        colored_image[x, y] = [255, 0, 0]  # Red for branch points

      # Convert the numpy array to an Image object
      final_image = Image.fromarray(colored_image)

      # Display the processed image with colored points
      self.processed_canvas.set_pil_image(final_image)
      self.save_button.config(state=tk.NORMAL)

  def save_image(self):
    file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG files", "*.png"),
                                                        ("JPEG files", "*.jpg"),
                                                        ("BMP files", "*.bmp")])
    if file_path:
      self.processed_canvas.pil_image.save(file_path)
      messagebox.showinfo("Image Saved",
                          f"Processed image saved at {file_path}")


if __name__ == "__main__":
  root = tk.Tk()
  app = ImageSkeletonApp(root)
  root.mainloop()
