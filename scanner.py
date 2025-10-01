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
BLUE_THRESHOLD = 120

SCREEN_CORNER_X = 691
SCREEN_CORNER_Y = 346
BOARD_SIZE_X = 595
BOARD_SIZE_Y = 525

screen_region = (SCREEN_CORNER_X, SCREEN_CORNER_Y, BOARD_SIZE_X, BOARD_SIZE_Y)

TARGET_SIZE_X = BOARD_SIZE_X // COLS
TARGET_SIZE_Y = BOARD_SIZE_Y // ROWS

target_region = (691, 346,  TARGET_SIZE_X, TARGET_SIZE_Y)

# In HSV: H = 0–179, S = 0–255, V = 0–255

blue_color_ranges = {
    "blue":  ([100, 50, 50], [130, 255, 255]),
}

red_color_ranges = {
    "red":   [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [179, 255, 255])],
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

blue_mask = np.zeros((1, TARGET_SIZE_X, TARGET_SIZE_Y), dtype=np.uint8)
frame = capture_region(target_region)
get_color_masks(frame, blue_color_ranges, blue_mask)

i = 1;
targets = [(7,16), (14, 16), (14, 0), (0, 0), (0,16)]
instructions = ["down", "left", "up", "right", "down"]

target_region = (TARGET_SIZE_X * targets[0][1] + 691, TARGET_SIZE_Y * targets[0][0] + 346,  TARGET_SIZE_X, TARGET_SIZE_Y)

while(True):

    blue_mask = np.zeros((1, TARGET_SIZE_X, TARGET_SIZE_Y), dtype=np.uint8)
    frame = capture_region(target_region)
    get_color_masks(frame, blue_color_ranges, blue_mask)

    blue_mean = blue_mask.mean()
#    print(blue_mean)

    if(blue_mean > BLUE_THRESHOLD):
        pyautogui.press(instructions[i-1])
        target_region = (TARGET_SIZE_X * targets[i][1] + 691, TARGET_SIZE_Y * targets[i][0] + 346,  TARGET_SIZE_X, TARGET_SIZE_Y)
        print(target_region)
        i = (i+1) % 5
