import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

from image_components import PanZoomCanvas
from image_utils import binarize_image
from skeletonization import hilditch_skeletonize, skeletonize


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
                                    command=self.process_image)
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
                   value=0).pack(
      side=tk.LEFT)
    tk.Radiobutton(self.bg_frame, text="White", variable=self.bg_color,
                   value=1).pack(
      side=tk.LEFT)

    # Frame for side-by-side canvases
    self.canvas_frame = tk.Frame(root)
    self.canvas_frame.pack(pady=10, expand=True)

    # Original and Processed PanZoomCanvas placeholders
    self.original_canvas = PanZoomCanvas(self.canvas_frame)
    self.original_canvas.grid(row=0, column=0, padx=5, pady=5)
    self.processed_canvas = PanZoomCanvas(self.canvas_frame)
    self.processed_canvas.grid(row=0, column=1, padx=5, pady=5)

  #   # Initial background update
  #   self.update_background()
  #
  # def update_background(self):
  #   """Updates the background color of both canvases based on selection."""
  #   bg_color = self.bg_color.get()
  #   bg_color_name = "black"
  #   if bg_color:
  #     bg_color_name = "white"
  #   self.original_canvas.canvas.config(background=bg_color_name)
  #   self.processed_canvas.canvas.config(background=bg_color_name)

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

  def process_image(self):
    if self.original_canvas.pil_image:
      binary_image = np.array(
        binarize_image(self.original_canvas.pil_image.convert("L"), 200)) // 255
      skeleton = hilditch_skeletonize(binary_image, self.bg_color.get()) * 255
      processed_image = Image.fromarray(skeleton.astype(np.uint8))
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
