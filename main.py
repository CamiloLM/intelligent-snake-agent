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
            [Pos(8, 5), Pos(8, 4), Pos(8, 3), Pos(8, 2)],
            [PointType.HEAD_D] + [PointType.BODY_HOR] * 3,
        )
        self.solver = GreedySolver(self.snake)

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
        # self.test_scanner_accuracy()
        n = 0
        while n < 20:
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
    time.sleep(0.3)

    agent.run()
