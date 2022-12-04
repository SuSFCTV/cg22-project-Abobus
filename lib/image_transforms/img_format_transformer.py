from PIL import Image
from tkinter import simpledialog
from numba import njit
import numpy as np

from lib.image_transforms.image_kernels import padding, bicubic_kernel, lanczos_filter
from lib.singleton_objects import ImageObjectSingleton, UISingleton
from lib.image_managers import ImageViewer
import math


class ImgFormatTransformer:
    """
    A class that doing some geometric transformation with image
    """

    @staticmethod
    def rotate():  # TODO: поменять на numpy
        """
        Rotates the image 90 degrees
        : return: None
        """
        ImageObjectSingleton.img = ImageObjectSingleton.img.rotate(90)
        ImageViewer.display_img()

    @staticmethod
    def stash_changes():
        ImageObjectSingleton.img_array = ImageObjectSingleton.default_img
        ImageObjectSingleton.color = "RGB"
        for element in UISingleton.current_elements:
            UISingleton.canvas.delete(element)
        ImageViewer.display_img_array(ImageObjectSingleton.default_img)

    @staticmethod
    def flip() -> None:  # TODO: поменять на numpy
        """
        It mirrors the image horizontally
        : return: None
        """
        ImageObjectSingleton.img = ImageObjectSingleton.img.transpose(Image.FLIP_LEFT_RIGHT)
        ImageViewer.display_img()

    @staticmethod
    def get_pixel(source, col, row):
        r, g, b = source[:, :, 0].astype(float), source[:, :, 1].astype(float), source[:, :, 2].astype(float)
        return r[col][row], g[col][row], b[col][row]

    @staticmethod
    def resize_neighbour():
        img_array = ImageObjectSingleton.img_array
        height = int(simpledialog.askfloat(title="Type a height value", prompt="Try not to use big values",
                                       parent=UISingleton.ui_main))
        width = int(simpledialog.askfloat(title="Type a width value", prompt="Try not to use big values",
                                       parent=UISingleton.ui_main))
        original_width, original_height, channel = img_array.shape

        red_channel = img_array[:, :, 0]
        green_channel = img_array[:, :, 1]
        blue_channel = img_array[:, :, 2]

        resized_image = np.zeros((width, height, channel), dtype=np.uint8)

        x_scale = original_width / width
        y_scale = original_height / height

        resize_index_x = np.ceil(np.arange(0, original_width, x_scale)).astype(int)
        resize_index_y = np.ceil(np.arange(0, original_height, y_scale)).astype(int)
        resize_index_x[np.where(resize_index_x == original_width)] -= 1
        resize_index_y[np.where(resize_index_y == original_height)] -= 1

        resized_image[:, :, 0] = red_channel[resize_index_x, :][:, resize_index_y]
        resized_image[:, :, 1] = green_channel[resize_index_x, :][:, resize_index_y]
        resized_image[:, :, 2] = blue_channel[resize_index_x, :][:, resize_index_y]
        ImageObjectSingleton.img_array = resized_image
        ImageViewer.display_img_array(ImageObjectSingleton.img_array)

    @staticmethod
    def bilinear_resize():
        image = ImageObjectSingleton.img_array
        img_height, img_width = image.shape[:2]
        height = int(simpledialog.askfloat(title="Type a height value", prompt="Try not to use big values",
                                       parent=UISingleton.ui_main))
        width = int(simpledialog.askfloat(title="Type a width value", prompt="Try not to use big values",
                                       parent=UISingleton.ui_main))
        resized = np.array(Image.new('RGB', (width, height)))

        x_ratio = float(img_width - 1) / (width - 1) if width > 1 else 0
        y_ratio = float(img_height - 1) / (height - 1) if height > 1 else 0

        for i in range(height):
            for j in range(width):
                x_l, y_l = math.floor(x_ratio * j), math.floor(y_ratio * i)
                x_h, y_h = math.ceil(x_ratio * j), math.ceil(y_ratio * i)

                x_weight = (x_ratio * j) - x_l
                y_weight = (y_ratio * i) - y_l

                a = image[y_l, x_l]
                b = image[y_l, x_h]
                c = image[y_h, x_l]
                d = image[y_h, x_h]

                pixel = a * (1 - x_weight) * (1 - y_weight) \
                        + b * x_weight * (1 - y_weight) + \
                        c * y_weight * (1 - x_weight) + \
                        d * x_weight * y_weight

                resized[i][j] = pixel

        ImageObjectSingleton.img_array = resized
        ImageViewer.display_img_array(ImageObjectSingleton.img_array)

    @staticmethod
    def mitchell():
        height = int(simpledialog.askfloat(title="Type a height value", prompt="Try not to use big values",
                                           parent=UISingleton.ui_main))
        width = int(simpledialog.askfloat(title="Type a width value", prompt="Try not to use big values",
                                          parent=UISingleton.ui_main))
        B_m = simpledialog.askfloat(title="Type a B_m value", prompt="Try not to use big values", parent=UISingleton.ui_main)
        C_m = simpledialog.askfloat(title="Type a C_m value", prompt="Try not to use big values", parent=UISingleton.ui_main)
        img = ImageObjectSingleton.img_array
        H, W, C = img.shape

        x_ratio = float(W - 1) / (width - 1) if width > 1 else 0
        y_ratio = float(H - 1) / (height - 1) if height > 1 else 0

        img = padding(img, H, W, C)

        dH = height
        dW = width

        dst = np.zeros((dH, dW, 3))

        h_x, h_y = 1 * x_ratio, 1 * y_ratio

        for c in range(C):
            for j in range(dH):
                for i in range(dW):
                    # Getting the coordinates of the
                    # nearby values
                    x, y = i * h_x + 2, j * h_y + 2

                    x1 = 1 + x - math.floor(x)
                    x2 = x - math.floor(x)
                    x3 = math.floor(x) + 1 - x
                    x4 = math.floor(x) + 2 - x

                    y1 = 1 + y - math.floor(y)
                    y2 = y - math.floor(y)
                    y3 = math.floor(y) + 1 - y
                    y4 = math.floor(y) + 2 - y

                    # Considering all nearby 16 values
                    mat_l = np.matrix(
                        [[bicubic_kernel(x1, B_m, C_m), bicubic_kernel(x2, B_m, C_m), bicubic_kernel(x3, B_m, C_m),
                          bicubic_kernel(x4, B_m, C_m)]])
                    mat_m = np.matrix([[img[int(y - y1), int(x - x1), c],
                                        img[int(y - y2), int(x - x1), c],
                                        img[int(y + y3), int(x - x1), c],
                                        img[int(y + y4), int(x - x1), c]],
                                       [img[int(y - y1), int(x - x2), c],
                                        img[int(y - y2), int(x - x2), c],
                                        img[int(y + y3), int(x - x2), c],
                                        img[int(y + y4), int(x - x2), c]],
                                       [img[int(y - y1), int(x + x3), c],
                                        img[int(y - y2), int(x + x3), c],
                                        img[int(y + y3), int(x + x3), c],
                                        img[int(y + y4), int(x + x3), c]],
                                       [img[int(y - y1), int(x + x4), c],
                                        img[int(y - y2), int(x + x4), c],
                                        img[int(y + y3), int(x + x4), c],
                                        img[int(y + y4), int(x + x4), c]]])
                    mat_r = np.matrix(
                        [[bicubic_kernel(y1, B_m, C_m)], [bicubic_kernel(y2, B_m, C_m)], [bicubic_kernel(y3, B_m, C_m)],
                         [bicubic_kernel(y4, B_m, C_m)]])

                    # Here the dot function is used to get the dot
                    # product of 2 matrices
                    dst[j, i, c] = np.dot(np.dot(mat_l, mat_m), mat_r)

        ImageObjectSingleton.img_array = dst.astype(np.uint8)
        ImageViewer.display_img_array(ImageObjectSingleton.img_array)

    @staticmethod
    def lanczos():
        height = int(simpledialog.askfloat(title="Type a height value", prompt="Try not to use big values",
                                           parent=UISingleton.ui_main))
        width = int(simpledialog.askfloat(title="Type a width value", prompt="Try not to use big values",
                                          parent=UISingleton.ui_main))
        img = ImageObjectSingleton.img_array
        H, W, C = img.shape

        x_ratio = float(W - 1) / (width - 1) if width > 1 else 0
        y_ratio = float(H - 1) / (height - 1) if height > 1 else 0

        img = padding(img, H, W, C)

        dH = height
        dW = width

        dst = np.zeros((dH, dW, 3))

        h_x, h_y = 1 * x_ratio, 1 * y_ratio

        for c in range(C):
            print(c)
            for j in range(dH):
                for i in range(dW):
                    # Getting the coordinates of the
                    # nearby values
                    x, y = i * h_x + 2, j * h_y + 2

                    x1 = 1 + x - math.floor(x)
                    x2 = x - math.floor(x)
                    x3 = math.floor(x) + 1 - x
                    x4 = math.floor(x) + 2 - x

                    y1 = 1 + y - math.floor(y)
                    y2 = y - math.floor(y)
                    y3 = math.floor(y) + 1 - y
                    y4 = math.floor(y) + 2 - y

                    # Considering all nearby 16 values
                    mat_l = np.matrix(
                        [[lanczos_filter(x1), lanczos_filter(x2), lanczos_filter(x3), lanczos_filter(x4)]])
                    mat_m = np.matrix([[img[int(y - y1), int(x - x1), c],
                                        img[int(y - y2), int(x - x1), c],
                                        img[int(y + y3), int(x - x1), c],
                                        img[int(y + y4), int(x - x1), c]],
                                       [img[int(y - y1), int(x - x2), c],
                                        img[int(y - y2), int(x - x2), c],
                                        img[int(y + y3), int(x - x2), c],
                                        img[int(y + y4), int(x - x2), c]],
                                       [img[int(y - y1), int(x + x3), c],
                                        img[int(y - y2), int(x + x3), c],
                                        img[int(y + y3), int(x + x3), c],
                                        img[int(y + y4), int(x + x3), c]],
                                       [img[int(y - y1), int(x + x4), c],
                                        img[int(y - y2), int(x + x4), c],
                                        img[int(y + y3), int(x + x4), c],
                                        img[int(y + y4), int(x + x4), c]]])
                    mat_r = np.matrix(
                        [[lanczos_filter(y1)], [lanczos_filter(y2)], [lanczos_filter(y3)], [lanczos_filter(y4)]])

                    # Here the dot function is used to get the dot
                    # product of 2 matrices
                    dst[j, i, c] = np.dot(np.dot(mat_l, mat_m), mat_r)

        ImageObjectSingleton.img_array = dst.astype(np.uint8)
        ImageViewer.display_img_array(ImageObjectSingleton.img_array)
