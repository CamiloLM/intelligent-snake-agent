import cv2
import mss
import sys
import numpy as np

ROWS, COLS = 15, 17

red_color_ranges = {
    "red":   [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [179, 255, 255])],
}

def capture_region(region):
    left, top, width, height = region
    with mss.mss() as sct:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(monitor)  # raw BGRA image
        img = np.array(shot)      # make it a NumPy array
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # convert to BGR
        return img_bgr

def get_color_masks(img_bgr, color_ranges, masks_out=None):
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

def ratio_blocks(masks_stack, block_size=(35, 35), grid_shape=(ROWS, COLS)):
    block_h, block_w = block_size
    rows, cols = grid_shape
    num_colors, H, W = masks_stack.shape

    # Reshape: (colors, rows, block_h, cols, block_w)
    reshaped = masks_stack.reshape(num_colors, rows, block_h, cols, block_w)

    # Average over block pixels (axis 2,4) → ratios per block
    results = reshaped.mean(axis=(2, 4))

    return results

def capture_apple_coord(screen_region, block_size):
    red_mask = np.zeros((1, screen_region[3], screen_region[2]), dtype=np.uint8)
    frame = capture_region(screen_region)
    get_color_masks(frame, red_color_ranges, red_mask)
    red_cells_ratios = ratio_blocks(red_mask, block_size)
    max_idx = np.unravel_index(np.argmax(red_cells_ratios), red_cells_ratios.shape)
    return (max_idx[1], max_idx[2])

def calibrate_region(screen_region):
    frame = capture_region(screen_region)
    cv2.imwrite("calibrate_board.png", frame)

def main(screen_corner_x, screen_corner_y, board_size_x, board_size_y):
    screen_region = (int(screen_corner_x), int(screen_corner_y), int(board_size_x), int(board_size_y))
    block_size = ((screen_region[3]//ROWS, screen_region[2]//COLS))
    calibrate_region(screen_region)
    print("In the start position this should be (7, 12)")
    print(capture_apple_coord(screen_region, block_size))

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python scanner.py screen_corner_x screen_corner_y board_size_x board_size_y")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

