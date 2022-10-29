import re
import cv2

import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, Menu
import numpy as np
from loguru import logger

from lib.utils import enforce

mains = tk.Tk()
mains.geometry("1200x900")
mains.bg = "BLUE"
mains.title("Image editor")
img = None
img_array = None
COLOR = "RGB"  # by default


def read_img(verbose=False):
    global img_array
    """
        Reads in a PGM/PPM file by the given name and returns its contents in a new numpy
        ndarray with 8/16-bit elements. Also returns the maximum representable value of a
        pixel (typically 255, 1023, 4095, or 65535).
        """
    filespec = filedialog.askopenfilename(title="open")
    valid_extensions = [".pnm", ".ppm", ".pgm", ".PNM", ".PPM", ".PGM"]
    enforce(isinstance(filespec, str) and len(filespec) >= 5,
            "filespec must be a string of length >= 5, was %r." % (filespec))
    enforce(filespec[-4:] in valid_extensions,
            "file extension must be .pnm, .ppm, or .pgm; was %s." % (filespec[-4:]))
    with open(filespec, "rb") as f:
        buf = f.read()
        regex_pnm_header = b"(^(P[56])\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s)"
        match = re.search(regex_pnm_header, buf)
        if match is not None:
            header, typestr, width, height, maxval = match.groups()
            width, height, maxval = int(width), int(height), int(maxval)
            numch = 3 if typestr == b"P6" else 1
            shape = (height, width, numch) if typestr == b"P6" else (height, width)
            if verbose:
                logger.info("Reading file %s " % (filespec), end='')
                print("(w=%d, h=%d, c=%d, maxval=%d)" % (width, height, numch, maxval))
            dtype = ">u2" if maxval > 255 else np.uint8
            pixels = np.frombuffer(buf, dtype, count=width * height * numch, offset=len(header))
            pixels = pixels.reshape(shape).astype(np.uint8 if maxval <= 255 else np.uint16)
    img_array = pixels
    display_img_array(pixels)


def display_img_array(data: np.ndarray) -> None:
    global img
    img = Image.fromarray(data)
    display_img()


def display_img():
    dispimage = ImageTk.PhotoImage(img)
    panel.configure(image=dispimage)
    panel.image = dispimage


def rotate():  # TODO: поменять на numpy
    global img
    img = img.rotate(90)
    display_img()


def flip():  # TODO: поменять на numpy
    global img
    img = img.transpose(Image.FLIP_LEFT_RIGHT)
    display_img()


def save():
    global img
    imgname = filedialog.asksaveasfilename(title="save", defaultextension=".jpg")
    if imgname:
        img.save(imgname)


def change_to_hsl():
    pass


def change_to_hsv():
    global img_array
    if COLOR == "RGB":
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    display_img_array(img_array)


if __name__ == "__main__":
    panel = tk.Label(mains, bg="BLACK")
    panel.grid(row=0, column=0, rowspan=12, padx=50, pady=50)

    # btnOpen = tk.Button(mains, text='Open', width=25, command=read_img, bg="RED")
    # btnOpen.grid(row=0, column=1)
    #
    # btnRotate = tk.Button(mains, text='Rotate', width=25, command=rotate, bg="BLUE")
    # btnRotate.grid(row=1, column=1)
    #
    # btnFlip = tk.Button(mains, text='Flip', width=25, command=flip, bg="PINK")
    # btnFlip.grid(row=2, column=1)
    #
    # btnSave = tk.Button(mains, text='Save', width=25, command=save, bg="YELLOW")
    # btnSave.grid(row=3, column=1)

    main_menu = Menu(mains)
    mains.config(menu=main_menu)

    file_menu = Menu(main_menu, tearoff=0)
    file_menu.add_command(label="Open", command=read_img)
    file_menu.add_command(label="Rotate", command=rotate)
    file_menu.add_command(label="Flip", command=flip)
    file_menu.add_command(label="Save", command=save)

    color_menu = Menu(main_menu, tearoff=0)
    color_menu.add_command(label="RGB")
    color_menu.add_command(label="HSL")
    color_menu.add_command(label="HSV", command=change_to_hsv)
    color_menu.add_command(label="YCbCr.601")
    color_menu.add_command(label="YCbCr.709")
    color_menu.add_command(label="YCoCg")
    color_menu.add_command(label="CMY")

    main_menu.add_cascade(label="File",
                          menu=file_menu)
    main_menu.add_cascade(label="Colors",
                          menu=color_menu)

    mains.mainloop()
