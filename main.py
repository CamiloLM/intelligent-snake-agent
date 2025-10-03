import os
import time
from typing import Tuple

import cv2
import pyautogui

from actuator import Actuator
from base import Direc, Map, PointType, Pos, Snake
from scanner import Scanner


class Agent:
    def __init__(self, region: Tuple):
        self._scanner = Scanner(region)
        self._actuator = Actuator()
        self._map = Map(17, 19)
        # self._solver = GreedySolver()

    def restart(self):
        """Se reinicia a la posición inicial del juego"""
        self._map.create_food(Pos(7, 13))
        init_body = [Pos(8, 7), Pos(8, 6), Pos(8, 5)]
        init_types = [PointType.HEAD_R, PointType.BODY_HOR, PointType.BODY_HOR]
        self._snake = Snake(self._map, Direc.NONE, init_body, init_types)

    def run(self):
        self.test_scanner_accuracy()
        # start_time = time.time()
        # end_time = time.time()
        # execution_time = end_time - start_time

    def test_scanner_accuracy(self):
        self._scanner.save_multiple_images(0.1235, 100)

        folder_name = "screenshots"
        if os.path.isdir(folder_name):
            if not os.listdir(folder_name):
                raise ValueError("La carpeta screenshots esta vacia")
            else:
                for file_name in os.listdir(folder_name):
                    img_bgr = self._scanner.load_image(
                        os.path.join(folder_name, file_name)
                    )
                    pos = self._scanner.apple_coords(img_bgr)
                    self.add_black_rectangle(
                        file_name, (pos.x * 32, pos.y * 32, 32, 32)
                    )
        else:
            raise ValueError("No hay carpeta screenshots")

    def add_black_rectangle(self, file_name, position):
        # Load the image from the file path
        img = cv2.imread(os.path.join("./screenshots", file_name))

        # position is a tuple of (x, y, width, height)
        x, y, w, h = position

        # Draw a black rectangle (BGR format for color, black = (0, 0, 0))
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0))

        # Show the image
        cv2.imshow("Image with Rectangle", img)

        # Save the image to a new file (optional)
        base_name, ext = os.path.splitext(file_name)
        output_path = os.path.join("./analized/", base_name, "_mod", ext)
        cv2.imwrite(output_path, img)

        # Wait for a key press to close the image window
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    x1, y1 = 411, 237
    x2, y2 = 955, 717
    board_width = x2 - x1
    board_height = y2 - y1

    agent = Agent((x1, y1, board_width, board_height))

    if True:
        pyautogui.hotkey("alt", "tab")
        time.sleep(3)

    agent.run()
