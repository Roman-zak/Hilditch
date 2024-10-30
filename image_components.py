import tkinter as tk
import numpy as np
from PIL import Image, ImageTk

class PanZoomCanvas(tk.Frame):
    def __init__(self, master, canvas_w=512, canvas_h=768):
        super().__init__(master)
        self.pil_image = None  # Image data to be displayed
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.create_widget(canvas_w, canvas_h)  # Create canvas
        self.reset_transform()  # Initial affine transformation matrix
        self.min_scale = 0.1  # Minimum scale to prevent excessive zoom out
        self.max_scale = 10.0  # Maximum scale to prevent excessive zoom in

    def create_widget(self, width, height):
        # Canvas
        self.canvas = tk.Canvas(self, background="black", width=width, height=height)
        self.canvas.pack(expand=True, fill="both")
        # Controls
        self.canvas.bind("<Button-1>", self.mouse_down_left)
        self.canvas.bind("<B1-Motion>", self.mouse_move_left)
        self.canvas.bind("<Double-Button-1>", self.mouse_double_click_left)
        self.canvas.bind("<MouseWheel>", self.mouse_wheel)

    def set_image(self, filename):
        '''To open an image file'''
        if not filename:
            return
        self.pil_image = Image.open(filename)
        # Adjust canvas size to match the aspect ratio of the image
        self.adjust_canvas_to_image()
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.redraw_image()

    def adjust_canvas_to_image(self):
        """Resize the canvas to maintain the image's aspect ratio."""
        img_width, img_height = self.pil_image.size
        aspect_ratio = img_width / img_height
        max_canvas_width = self.winfo_toplevel().winfo_width() // 2 - 20  # Allow for border padding
        max_canvas_height = self.winfo_toplevel().winfo_height() - 150  # Adjust for UI elements

        # Calculate new dimensions based on the max dimensions and aspect ratio
        if max_canvas_width / aspect_ratio <= max_canvas_height:
            new_canvas_width = max_canvas_width
            new_canvas_height = int(new_canvas_width / aspect_ratio)
        else:
            new_canvas_height = max_canvas_height
            new_canvas_width = int(new_canvas_height * aspect_ratio)

        # Resize the canvas to match the new dimensions
        self.canvas.config(width=new_canvas_width, height=new_canvas_height)

    def mouse_down_left(self, event):
        self.__old_event = event

    def mouse_move_left(self, event):
        if self.pil_image is None:
            return
        self.translate(event.x - self.__old_event.x, event.y - self.__old_event.y)
        self.redraw_image()
        self.__old_event = event

    def mouse_double_click_left(self, event):
        if self.pil_image is None:
            return
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.redraw_image()

    def mouse_wheel(self, event):
        """ Zoom in or out based on mouse wheel """
        if self.pil_image is None:
            return

        scale_factor = 1.25 if event.delta > 0 else 0.8
        new_scale = self.mat_affine[0, 0] * scale_factor

        # Limit the scaling to prevent excessive zooming in or out
        if self.min_scale < new_scale < self.max_scale:
            self.scale_at(scale_factor, event.x, event.y)
            self.redraw_image()

    def reset_transform(self):
        self.mat_affine = np.eye(3)

    def translate(self, offset_x, offset_y, zoom=False):
        mat = np.eye(3)
        mat[0, 2] = float(offset_x)
        mat[1, 2] = float(offset_y)
        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale(self, scale: float):
        mat = np.eye(3)
        mat[0, 0] = scale
        mat[1, 1] = scale
        self.mat_affine = np.dot(mat, self.mat_affine)

    def scale_at(self, scale: float, cx: float, cy: float):
        """ Scale the image around a specific point (cx, cy) """
        self.translate(-cx, -cy, True)
        self.scale(scale)
        self.translate(cx, cy)

    def zoom_fit(self, image_width, image_height):
        """ Adjust image to fit within canvas dimensions """
        self.master.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.reset_transform()
        scale = 1.0
        offsetx = offsety = 0.0
        if canvas_width * image_height > image_width * canvas_height:
            scale = canvas_height / image_height
            offsetx = (canvas_width - image_width * scale) / 2
        else:
            scale = canvas_width / image_width
            offsety = (canvas_height - image_height * scale) / 2
        self.scale(scale)
        self.translate(offsetx, offsety)

    def draw_image(self, pil_image):
        if pil_image is None:
            return
        self.pil_image = pil_image
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        mat_inv = np.linalg.inv(self.mat_affine)
        affine_inv = (
            mat_inv[0, 0], mat_inv[0, 1], mat_inv[0, 2],
            mat_inv[1, 0], mat_inv[1, 1], mat_inv[1, 2]
        )
        dst = self.pil_image.transform(
            (canvas_width, canvas_height),
            Image.AFFINE,
            affine_inv,
            Image.NEAREST
        )
        im = ImageTk.PhotoImage(image=dst)
        self.canvas.create_image(0, 0, anchor='nw', image=im)
        self.image = im

    def redraw_image(self):
        if self.pil_image is None:
            return
        self.draw_image(self.pil_image)

    def set_pil_image(self, pil_image):
        """Set a PIL image directly."""
        self.pil_image = pil_image
        self.adjust_canvas_to_image()
        self.zoom_fit(self.pil_image.width, self.pil_image.height)
        self.redraw_image()
