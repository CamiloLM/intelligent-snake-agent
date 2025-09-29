import cv2
import mss
import numpy as np
import time
from . import superReadScore

import pyautogui
import random


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

def ratio_blocks(masks_stack, block_size=(35, 35), grid_shape=(15, 17)):
    block_h, block_w = block_size
    rows, cols = grid_shape
    total_pixels = block_h * block_w
    num_colors, H, W = masks_stack.shape

    results = np.zeros((num_colors, rows, cols), dtype=np.float32)

    for ci in range(num_colors):
        mask = (masks_stack[ci] // 255).astype(np.uint8)

        # integral shape = (H+1, W+1)
        integral = cv2.integral(mask)

        for r in range(rows):
            for c in range(cols):
                y1 = r * block_h
                y2 = y1 + block_h
                x1 = c * block_w
                x2 = x1 + block_w

                # Shift coords by +1 for integral indexing
                block_sum = (
                    integral[y2, x2]
                    - integral[y1, x2]
                    - integral[y2, x1]
                    + integral[y1, x1]
                )

                results[ci, r, c] = block_sum / total_pixels

    return results

def ratio_blocks_v2(masks_stack, block_size=(35, 35), grid_shape=(15, 17)):
    """
    Compute block fill ratios for stacked binary masks using padded integral images.

    Args:
      masks_stack: ndarray (num_colors, H, W) dtype=uint8 (0 or 255)
      block_size: (block_h, block_w)
      grid_shape: (rows, cols)

    Returns:
      ratios: ndarray (num_colors, rows, cols) float32 in [0,1]
    """
    block_h, block_w = block_size
    rows, cols = grid_shape
    total_pixels = block_h * block_w

    num_colors, H, W = masks_stack.shape
    # Convert to binary 0/1 (uint32 for safe accumulation)
    binary = (masks_stack > 0).astype(np.uint32)  # shape (num_colors, H, W)

    # Build padded integral: shape (num_colors, H+1, W+1)
    # integral[:, y, x] = sum of binary[:, 0..y-1, 0..x-1]
    integral = np.zeros((num_colors, H + 1, W + 1), dtype=np.uint32)
    # place cumsum result starting at 1,1 so indexing matches formula above
    integral[:, 1:, 1:] = binary.cumsum(axis=1).cumsum(axis=2)

    # Prepare output
    ratios = np.zeros((num_colors, rows, cols), dtype=np.float32)

    # For each block compute sum via 4 lookups into padded integral
    for r in range(rows):
        y1 = r * block_h
        y2 = y1 + block_h
        for c in range(cols):
            x1 = c * block_w
            x2 = x1 + block_w

            # Use the padded integral indices directly
            # block_sum for all colors at once -> shape (num_colors,)
            block_sum = (
                integral[:, y2, x2]
                - integral[:, y1, x2]
                - integral[:, y2, x1]
                + integral[:, y1, x1]
            )

            ratios[:, r, c] = block_sum.astype(np.float32) / float(total_pixels)

    return ratios

def ratio_blocks_v3(masks_stack, block_size=(35, 35), grid_shape=(15, 17)):
    block_h, block_w = block_size
    rows, cols = grid_shape
    num_colors, H, W = masks_stack.shape

    # Reshape: (colors, rows, block_h, cols, block_w)
    reshaped = masks_stack.reshape(num_colors, rows, block_h, cols, block_w)

    # Average over block pixels (axis 2,4) → ratios per block
    results = reshaped.mean(axis=(2, 4))

    return results

def press_random_wasd(last_key):
    keys = ["w", "a", "s", "d"]

    # pick a new key different from last one
    choices = [k for k in keys if k != last_key]
    key = random.choice(choices)

    pyautogui.press(key)
    last_key = key
    return key  # optional, to know what was pressed

def run_loop(screen_region, color_ranges, fps=24):
    period = 1.0 / fps
    prev_eyes_coord = (-1, -1)

    # One-time setup: capture shape + preallocate
    test_frame = capture_region(screen_region)
    H, W, _ = test_frame.shape
    num_colors = len(color_ranges)
    masks_stack = np.zeros((num_colors, H, W), dtype=np.uint8)

    color_names = list(color_ranges.keys())
    white_idx = color_names.index("white")  # <-- lookup only once

    prev_max_val = 0
    last_key = "d"

    while True:
        #start = time.time()

        frame = capture_region(screen_region)
        if frame is not None:
            # Fill into preallocated stack
            get_color_masks(frame, color_ranges, masks_stack)

            # Compute ratios
            #ratios = ratio_blocks(masks_stack)
            #ratios = ratio_blocks_v2(masks_stack)
            ratios = ratio_blocks_v3(masks_stack)

            # Grab white matrix directly
            white_matrix = ratios[white_idx]
            max_idx = np.unravel_index(np.argmax(white_matrix), white_matrix.shape)
            max_val = white_matrix[max_idx]

            if prev_max_val < max_val:
            #if True:
                currentScore = superReadScore.capture(superReadScore.SCREEN_REGION,
                                                  superReadScore.templates_bin,
                                                  digit_w=superReadScore.DIGIT_W)
                print(f"Max:({max_idx[0]}, {max_idx[1]}) ratio={max_val:.3f} score=",currentScore)
                #press_random_wasd(last_key)
                if prev_eyes_coord != max_idx:
#wrong , if a coord in the vincinity has risen in value, eyes there
                    prev_eyes_coord = max_idx
            prev_max_val = max_val

            #if True:
                #prevEyesCoord = max_idx

            # call the capture function directly
            #    currentScore = superReadScore.capture(superReadScore.SCREEN_REGION,
            #                                      superReadScore.templates_bin,
            #                                      digit_w=superReadScore.DIGIT_W)
#                print("Captured currentScore:", currentScore)
                            # event happens!

            #elapsed = time.time() - start
            #sleep_time = max(0, period - elapsed)
            #time.sleep(sleep_time)

if __name__ == '__main__':
    run_loop(screen_region, color_ranges)
