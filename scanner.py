import os
import shutil
import time

import cv2
import numpy as np
import pyautogui

from base.point import PointType


class Scanner:
    def __init__(self, region, cell_size=35, screenshot_dir="screenshots"):
        self.region = region
        self.cell_size = cell_size
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)

    # --- Gestión de screenshots ---
    def _clear_screenshots(self):
        if os.path.exists(self.screenshot_dir):
            shutil.rmtree(self.screenshot_dir)
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def capture_board(self):
        screenshot = pyautogui.screenshot(region=self.region)
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return img

    def save_screenshot(self, img, name="board.png"):
        path = os.path.join(self.screenshot_dir, name)
        cv2.imwrite(path, img)
        return path

    # --- Detección fin del juego ---
    def is_game_over(self, img):
        """Detecta si aparece un color cercano a #4dc1f9 (azul celeste)."""
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array([95, 50, 180])  # tolerancia alrededor de #4dc1f9
        upper = np.array([105, 150, 255])
        mask = cv2.inRange(hsv, lower, upper)
        ratio = np.count_nonzero(mask) / (img.shape[0] * img.shape[1])
        return ratio > 0.01  # si ocupa >1% de la pantalla, asumimos game over

    # --- Clasificación por color ---
    def clasificar_color(self, cell_img):
        hsv = cv2.cvtColor(cell_img, cv2.COLOR_BGR2HSV)
        total = cell_img.shape[0] * cell_img.shape[1]

        green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        red_mask1 = cv2.inRange(hsv, (0, 120, 50), (10, 255, 255))
        red_mask2 = cv2.inRange(hsv, (160, 120, 50), (180, 255, 255))
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        blue_mask = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
        white_mask = cv2.inRange(hsv, (0, 0, 200), (180, 60, 255))

        green_ratio = np.count_nonzero(green_mask) / total
        red_ratio = np.count_nonzero(red_mask) / total
        blue_ratio = np.count_nonzero(blue_mask) / total
        white_ratio = np.count_nonzero(white_mask) / total

        if green_ratio > 0.50:
            return PointType.EMPTY
        if red_ratio > 0.05:
            return PointType.FOOD
        if white_ratio > 0.08:
            return PointType.HEAD_U
        if blue_ratio > 0.05:
            return PointType.BODY_VER

        v_mean = hsv[:, :, 2].mean()
        s_mean = hsv[:, :, 1].mean()
        if v_mean > 200 and s_mean < 60:
            return PointType.HEAD_U

        return None

    def detectar_celda(self, cell_img):
        return self.clasificar_color(cell_img)

    # --- Construcción de la grilla ---
    def mapear_grid(self, board, rows=15, cols=17):
        grid = []
        for i in range(rows):
            fila = []
            for j in range(cols):
                cell = board[
                    i * self.cell_size : (i + 1) * self.cell_size,
                    j * self.cell_size : (j + 1) * self.cell_size,
                ]
                point_type = self.detectar_celda(cell)
                fila.append(point_type)
            grid.append(fila)
        return grid

    # --- Depuración grilla simplificada ---
    @staticmethod
    def simplificar(point):
        if point == PointType.EMPTY:
            return "E"
        if point == PointType.FOOD:
            return "F"
        if point in (
            PointType.HEAD_L,
            PointType.HEAD_R,
            PointType.HEAD_U,
            PointType.HEAD_D,
        ):
            return "H"
        if point.value >= 104:  # cuerpos / cola
            return "B"
        return "?"

    def print_grid(self, grid):
        for fila in grid:
            print(" ".join(self.simplificar(p) for p in fila))


if __name__ == "__main__":
    REGION = (387, 217, 594, 525)
    FPS = 120

    scanner = Scanner(region=REGION)
    scanner._clear_screenshots()

    pyautogui.hotkey("alt", "tab")
    time.sleep(0.6)

    frame = 0
    while True:
        board = scanner.capture_board()

        # Fin del juego
        if scanner.is_game_over(board):
            print("⚠️  Game Over detectado.")
            break

        # Guardar screenshot
        fname = f"frame_{frame:04d}.png"
        scanner.save_screenshot(board, fname)

        # Grilla
        grid = scanner.mapear_grid(board)
        print(f"\n--- Frame {frame} ---")
        scanner.print_grid(grid)

        frame += 1
        time.sleep(1 / FPS)

    print("Scanner terminado.")
