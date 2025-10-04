import os
import time
from typing import Tuple

import cv2
import pyautogui

from actuator import Actuator
from base import Direc, Map, PointType, Pos, Snake
from scanner import Scanner
from solver import GreedySolver

X, Y = 411, 237
# x2, y2 = 955, 717

WIDTH = 544
HEIGHT = 480

ROWS = 15
COLS = 17

CELL_SIZE = WIDTH // COLS


class Agent:
    def __init__(self, region: Tuple):
        self.scanner = Scanner(region)
        self.actuator = Actuator()
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


if __name__ == "__main__":
    x1, y1 = 411, 237
    x2, y2 = 955, 717
    board_width = x2 - x1
    board_height = y2 - y1

    agent = Agent((x1, y1, board_width, board_height))

    pyautogui.hotkey("alt", "tab")
    time.sleep(1)

    agent.run()
