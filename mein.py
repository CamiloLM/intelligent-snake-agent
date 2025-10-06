import os
import time
from typing import Tuple

import cv2
import pyautogui

from actuator import Actuator
from base import Direc, Map, PointType, Pos, Snake
from scanner import Scanner
from solver import GreedySolver

import cv2
import mss
import sys
import numpy as np
import pyautogui

ROWS, COLS = 15, 17
BLUE_THRESHOLD = 150

#X, Y = 411, 237
# x2, y2 = 955, 717

#WIDTH = 544
#HEIGHT = 480

#ROWS = 15
#COLS = 17

#CELL_SIZE = WIDTH // COLS

red_color_ranges = {
    "red":   [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [179, 255, 255])],
}

blue_color_ranges = {
    "blue":  ([100, 50, 50], [130, 255, 255]),
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

def calibrate_region(screen_region):
    frame = capture_region(screen_region)
    cv2.imwrite("calibrate_board.png", frame)

def target_in_apple_zone(target_coord, apple_coord):
    return abs(target_coord[0]-apple_coord[0]) <= 2 and abs(target_coord[1]-apple_coord[1]) <= 2

class Agent:
    def __init__(self):
        #self.scanner = Scanner(region)
        #self.actuator = Actuator()
        self.map = Map(17, 19)
        self.snake = Snake(
            self.map,
            Direc.RIGHT,
            [Pos(8, 5), Pos(8, 4), Pos(8, 3), Pos(8, 2)],
            [PointType.HEAD_D] + [PointType.BODY_HOR] * 3,
        )
        self.solver = GreedySolver(self.snake)

    def generate_screenshots(self):
        delay = 0.1235
        num_images = 20

        self.scanner.save_multiple_images(delay, num_images)

    def test_scanner_accuracy(self):
        folder_name = "screenshots"
        if os.path.isdir(folder_name):
            if not os.listdir(folder_name):
                raise ValueError("La carpeta screenshots esta vacia")
            else:
                for file_name in os.listdir(folder_name):
                    img_bgr = self.scanner.load_image(
                        os.path.join(folder_name, file_name)
                    )
                    food_pos = self.scanner.apple_coords(img_bgr)
                    x = (food_pos.y - 1) * CELL_SIZE
                    y = (food_pos.x - 1) * CELL_SIZE

                    self.add_black_rectangle(file_name, (x, y, CELL_SIZE, CELL_SIZE))
        else:
            raise ValueError("No hay carpeta screenshots")

    def add_black_rectangle(self, file_name, position):
        img = cv2.imread(os.path.join("./screenshots", file_name))

        x, y, w, h = position
        # Dibuja un rectangulo negro en la posición de la comida
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0))

        cv2.imshow("Image with Rectangle", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def compute(self, percept):
        """
        Computa las percepciones que le manda el sensor y envia una accion al actuador
        """
        # Caso 1: El sensor le envio una posición
        if isinstance(percept, Pos):
            # La serpiente econtro la comida
            self.map.rm_food()
            self.map.create_food(percept)

            print(f"Food: {self.map.food}")
            new_direc = self.solver.next_direc()
            print(f"Cabeza: {self.snake.head()}")
            print(f"Direc: {new_direc}")

            self.snake.move(new_direc)

            return new_direc
        else:
            print(f"Percepcion: {percept}")
            raise "Percepcion no esperada"

    def run(self):
        self.generate_screenshots()
        self.test_scanner_accuracy()

        n = 0
        while n < 0:
            print(f"\nIntento numero {n}")
            # start_time = time.time()
            img_bgr = self.scanner.capture_region()
            food_pos = self.scanner.apple_coords(img_bgr)
            action = self.compute(food_pos)
            # print(action)
            # end_time = time.time()
            self.actuator.send(action)
            # execution_time = end_time - start_time
            # print(f"Tiempo de ejecución {execution_time}\n")
            time.sleep(0.04)
            n += 1


def main():
    agent = Agent()

    targets = [(14, 16), (14, 0), (0, 0), (0,16)]
    instructions = ["left", "up", "right", "down"]

    screen_region = (691, 346, 595, 525)
    target_region = (35 * targets[0][1] + 691, 35 * targets[0][0] + 346,  35, 35)

    block_size = ((35, 35))

    red_mask = np.zeros((1, screen_region[3], screen_region[2]), dtype=np.uint8)
    blue_mask = np.zeros((1, block_size[0], block_size[1]), dtype=np.uint8)

    i = 0
    while(True):
        frame = capture_region(screen_region)
        get_color_masks(frame, red_color_ranges, red_mask)
        red_cells_ratios = ratio_blocks(red_mask, block_size)
        apple_coord = np.unravel_index(np.argmax(red_cells_ratios), red_cells_ratios.shape)

        trap_frame = capture_region(target_region)
        get_color_masks(trap_frame, blue_color_ranges, blue_mask)
        blue_mean = blue_mask.mean()

        if(blue_mean > BLUE_THRESHOLD):
            pyautogui.press(instructions[i%len(instructions)])
            target_region = (35 * targets[(i+1)%(len(instructions))][1] + 691, 35 * targets[(i+1)%(len(instructions))][0] + 346,  35, 35)
            #print(target_region)
            if (target_in_apple_zone(targets[(i+1)%(len(instructions))],apple_coord)):
                BLUE_THRESHOLD = 190
            else:
                BLUE_THRESHOLD = 120
            i = i+1

def direc_to_str(direc):
    match direc:
        case direc.UP:
            return "up"

        case direc.DOWN:
            return "down"

        case direc.LEFT:
            return "left"

        case direc.RIGHT:
            return "right"

if __name__ == '__main__':
    agent = Agent()
    agent.map.create_food(Pos(8, 13))
    last_direc = Direc.RIGHT
    next_direc = Direc.RIGHT

    while(next_direc == last_direc):
        agent.snake.move(next_direc)
        next_direc = agent.solver.next_direc()
    last_direc = next_direc

    targets = []
    instructions = []

    targets.append((agent.snake.head().x - 1, agent.snake.head().y - 1))
    instructions.append(direc_to_str(next_direc))

    screen_region = (691, 346, 595, 525)
    target_region = (35 * targets[0][1] + 691, 35 * targets[0][0] + 346,  35, 35)

    block_size = ((35, 35))

    red_mask = np.zeros((1, screen_region[3], screen_region[2]), dtype=np.uint8)
    blue_mask = np.zeros((1, block_size[0], block_size[1]), dtype=np.uint8)

    print(next_direc)
    print(targets[0])
    print("---")

    while(True):
        trap_frame = capture_region(target_region)
        get_color_masks(trap_frame, blue_color_ranges, blue_mask)
        blue_mean = blue_mask.mean()

        if(blue_mean > BLUE_THRESHOLD):
            pyautogui.press(instructions.pop())
            if (not agent.map.food):
                time.sleep(0.01)
                print("looked for food")
                frame = capture_region(screen_region)
                get_color_masks(frame, red_color_ranges, red_mask)
                red_cells_ratios = ratio_blocks(red_mask, block_size)
                apple_coord = np.unravel_index(np.argmax(red_cells_ratios), red_cells_ratios.shape)
                print(apple_coord[1], apple_coord[2])
                agent.map.create_food(Pos(apple_coord[1]+1, apple_coord[2] +1))
                print(agent.map.food)

            while(next_direc == last_direc):
                agent.snake.move(next_direc)
                next_direc = agent.solver.next_direc()

            instructions.append(direc_to_str(next_direc))
            print(next_direc)
            last_direc = next_direc

            targets.append((agent.snake.head().x - 1, agent.snake.head().y - 1))

            next_target = targets.pop()
            print(next_target)
            print("---")
            target_region = (35 * next_target[1] + 691, 35 * next_target[0] + 346,  35, 35)
            #print(target_region)
            if (target_in_apple_zone(next_target, apple_coord)):
                BLUE_THRESHOLD = 150
            else:
                BLUE_THRESHOLD = 120
