import os
import time
from typing import Tuple

import cv2
import pyautogui

from actuator import Actuator
from base import Direc, Map, PointType, Pos, Snake
from scanner import Scanner
from solver import GreedySolver


class Agent:
    def __init__(self, region: Tuple):
        self.scanner = Scanner(region)
        self.actuator = Actuator()
        self.map = Map(17, 19)
        self.snake = Snake(
            self.map,
            Direc.RIGHT,
            [Pos(5, 7), Pos(8, 6), Pos(8, 5)],
            [PointType.HEAD_R, PointType.BODY_HOR, PointType.BODY_HOR],
        )
        self.solver = GreedySolver(self.snake)

    def generate_screenshots(self):
        delay = 0.1235
        num_images = 100
        self.scanner.save_multiple_images(delay, num_images)

    def test_scanner_accuracy(self):
        folder_name = "screenshots"
        if os.path.isdir(folder_name):
            if not os.listdir(folder_name):
                raise ValueError("La carpeta screenshots esta vacia")
            else:
                for file_name in os.listdir(folder_name):
                    print(file_name)
                    img_bgr = self.scanner.load_image(
                        os.path.join(folder_name, file_name)
                    )
                    food_pos = self.scanner.apple_coords(img_bgr)
                    print(food_pos)
                    # TODO: Cambiar el tamaño de cell_sz por tamaño de la celda en .config
                    cell_sz = 32
                    x = (food_pos.x - 1) * cell_sz
                    y = (food_pos.y - 1) * cell_sz

                    self.add_black_rectangle(file_name, (x, y, cell_sz, cell_sz))
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

        # Wait for a key press to close the image window
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def compute(self, percept):
        """
        Computa las percepciones que le manda el sensor y envia una accion al actuador
        """
        # Caso 1: El sensor le envio una posición
        print(f"Percept: {percept}")
        if isinstance(percept, Pos):
            print(f"Cabeza: {self.snake.head()}")
            # La serpiente econtro la comida
            if percept != Pos(0, 0) and percept != Pos(16, 18):
                # La comida guardada no es la misma que la del sensor
                if self.map.has_food() and self.map.food != percept:
                    self.map.rm_food()
                    self.map.create_food(percept)
                # No hay comida en el mapa pero si hay en el sensor
                elif not self.map.has_food():
                    self.map.create_food(percept)

            print(f"Food: {self.map.food}")
            # new_direc = self.solver.next_direc()
            new_direc = Direc.RIGHT
            print(f"Direc: {new_direc}")

            self.snake.move(new_direc)
            print(f"Cabeza: {self.snake.head()}")

            return new_direc
        else:
            raise "Percepcion no esperada"

    def run(self):
        # self.test_scanner_accuracy()
        n = 0
        while n < 2:
            print(f"\nIntento numero {n}")
            # start_time = time.time()
            img_bgr = self.scanner.capture_region()
            food_pos = self.scanner.apple_coords(img_bgr)
            action = self.compute(food_pos)
            # end_time = time.time()
            self.actuator.send(action)
            # execution_time = end_time - start_time
            # print(f"Tiempo de ejecución {execution_time}\n")
            n += 1


if __name__ == "__main__":
    x1, y1 = 411, 237
    x2, y2 = 955, 717
    board_width = x2 - x1
    board_height = y2 - y1

    agent = Agent((x1, y1, board_width, board_height))

    pyautogui.hotkey("alt", "tab")
    time.sleep(0.3)

    agent.run()
