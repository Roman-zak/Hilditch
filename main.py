import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image
from image_components import PanZoomCanvas
from image_utils import binarize_image, binarize_channel
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


  def process_image(self):
    if self.original_canvas.pil_image:
      image = self.original_canvas.pil_image
      gray_image = image.convert("L")

      # Get the current threshold value from the slider
      threshold_value = self.threshold_slider.get()
      binary_image = np.array(
        binarize_image(gray_image, threshold_value)) // 255

      self.progress_bar["maximum"] = 100
      # Perform skeletonization
      skeleton = hilditch_skeletonize(binary_image, self.bg_color.get(), self.progress_bar) * 255

      processed_image = Image.fromarray(skeleton.astype(np.uint8))

      # Display the processed image
      self.processed_canvas.set_pil_image(processed_image)
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
