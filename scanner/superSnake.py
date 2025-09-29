import cv2
import mss
import numpy as np
import time
import superReadScore
import struct
import os

import pyautogui
import random

ROWS, COLS = 15, 17
fifo_py_to_c = "py_to_c.fifo"
fifo_c_to_py = "c_to_py.fifo"

screen_region = (691, 346, 595, 525)

# In HSV: H = 0–179, S = 0–255, V = 0–255

color_ranges = {
    "green": ([35, 40, 40], [85, 255, 255]),
    "blue":  ([100, 50, 50], [130, 255, 255]),
    "red":   [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [179, 255, 255])],
    "white": ([0, 0, 200], [179, 40, 255]),
}

def capture_region(region):
    """
    Capture a region of the screen and return it as a cv2-compatible image (NumPy array).

    region: (left, top, width, height)
    """
    left, top, width, height = region
    with mss.mss() as sct:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(monitor)  # raw BGRA image
        img = np.array(shot)      # make it a NumPy array
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # convert to BGR
        return img_bgr

def get_color_masks(img_bgr, color_ranges, masks_out=None):
    """
    Given a BGR image and a dictionary of color ranges, return a stacked mask array.

    Args:
        img_bgr: input image (H, W, 3) in BGR
        color_ranges: dict {color_name: [ (lower, upper), ... ]}
        masks_out: optional preallocated array (num_colors, H, W), dtype=uint8

    Returns:
        stacked masks of shape (num_colors, H, W), dtype=uint8
        and a list of color names in the same order.
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, w = hsv.shape[:2]
    color_names = list(color_ranges.keys())
    num_colors = len(color_names)

    if masks_out is None:
        masks_out = np.zeros((num_colors, h, w), dtype=np.uint8)

    for i, color in enumerate(color_names):
        ranges = color_ranges[color]

        if isinstance(ranges[0][0], int):
            # single range
            lower, upper = ranges
            cv2.inRange(hsv, np.array(lower), np.array(upper), dst=masks_out[i])
        else:
            # multiple ranges → OR them together
            temp_mask = np.zeros((h, w), dtype=np.uint8)
            for lower, upper in ranges:
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                cv2.bitwise_or(temp_mask, mask, dst=temp_mask)
            masks_out[i][:] = temp_mask

    return masks_out, color_names

def ratio_blocks_v3(masks_stack, block_size=(35, 35), grid_shape=(15, 17)):
    block_h, block_w = block_size
    rows, cols = grid_shape
    num_colors, H, W = masks_stack.shape

    # Reshape: (colors, rows, block_h, cols, block_w)
    reshaped = masks_stack.reshape(num_colors, rows, block_h, cols, block_w)

    # Average over block pixels (axis 2,4) → ratios per block
    results = reshaped.mean(axis=(2, 4))

    return results

test_frame = capture_region(screen_region)
H, W, _ = test_frame.shape
num_colors = len(color_ranges)
masks_stack = np.zeros((num_colors, H, W), dtype=np.uint8)

color_names = list(color_ranges.keys())
blue_idx = color_names.index("blue")  # <-- lookup only once
red_idx = color_names.index("red")  # <-- lookup only once

# Create FIFOs if not present
for fifo in (fifo_py_to_c, fifo_c_to_py):
    if not os.path.exists(fifo):
        os.mkfifo(fifo)

# open FIFOs once
fd_out = open(fifo_py_to_c, "wb", buffering=0)
fd_in  = open(fifo_c_to_py, "rb", buffering=0)

while (True):
    frame = capture_region(screen_region)
    get_color_masks(frame, color_ranges, masks_stack)
    ratios = ratio_blocks_v3(masks_stack)

# Grab blue matrix directly
    blue_matrix = ratios[blue_idx]
    red_matrix = ratios[red_idx]

    max_idx = np.unravel_index(np.argmax(red_matrix), red_matrix.shape)
    max_red_val = red_matrix[max_idx]
    if (max_red_val < 120):
        max_ixd = (-1, -1)

    current_score = superReadScore.capture(superReadScore.SCREEN_REGION,
                                      superReadScore.templates_bin,
                                      digit_w=superReadScore.DIGIT_W)
    #print(f"Max:({max_idx[0]}, {max_idx[1]}) ratio={max_val:.3f} score=",current_score)

# Example matrix (replace with your blue_matrix)
    blue_matrix = blue_matrix.astype(np.float32)

# Example metadata (3 ints at the end)
    extra_info = (max_idx[0], max_idx[1], current_score)

# Build payload
    payload = blue_matrix.tobytes() + struct.pack("3i", *extra_info)

# Open fifo for writing
    #fd_out.write(blue_matrix.tobytes())         # matrix as float32 raw
    #fd_out.write(struct.pack("3i", *extra_info)) # 3x int32
    fd_out.write(payload)

# Read response back from C
    data = fd_in.read(4)
    (response,) = struct.unpack("i", data)
    if (response != 0):
        print("Got response from C:", response)

fd_out.close()
fd_in.close()
