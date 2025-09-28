import os
import shutil
from collections import Counter, deque
from typing import List

import cv2
import numpy as np
import pyautogui

from base import PointType


class Scanner:
    """
    Sensor: captura pantalla, construye grilla de PointType y estabiliza (debounce).
    - region: region para pyautogui.screenshot (x,y,w,h)
    - rows, cols: dimensiones del área jugable (ej. 15x17)
    - cell_size: tamaño en píxeles de cada celda
    - screenshot_dir: carpeta donde se guardan screenshots
    - debounce_frames: cuántos frames usar para estabilizar (ej. 3)
    """

    def __init__(
        self,
        region: tuple,
        rows: int = 15,
        cols: int = 17,
        cell_size: int = 35,
        screenshot_dir: str = "screenshots",
        debounce_frames: int = 3,
    ):
        self.region = region
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.screenshot_dir = screenshot_dir
        self.debounce_frames = max(1, int(debounce_frames))
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # almacenamiento temporal de últimos grids para debounce
        self._last_grids = deque(maxlen=self.debounce_frames)

    # ---- screenshots management ----
    def clear_screenshots(self):
        """Borra todo en la carpeta de screenshots (llamar al inicio de run)."""
        if os.path.exists(self.screenshot_dir):
            shutil.rmtree(self.screenshot_dir)
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def capture_board(self) -> np.ndarray:
        """Toma screenshot de la región y devuelve BGR np.array."""
        screenshot = pyautogui.screenshot(region=self.region)
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return img

    # alias más corto
    def capture(self) -> np.ndarray:
        """Atajo para capture_board()."""
        return self.capture_board()

    def save_screenshot(self, img: np.ndarray, name: str):
        """Guarda screenshot en screenshot_dir con el nombre indicado."""
        path = os.path.join(self.screenshot_dir, name)
        cv2.imwrite(path, img)
        return path

    # ---- game over detection (color ~ #4dc1f9) ----
    def is_game_over(self, img: np.ndarray, min_ratio: float = 0.01) -> bool:
        """
        Detecta color cercano a #4dc1f9. Devuelve True si ocupa > min_ratio de la imagen.
        """
        rgb = np.uint8([[[0x4D, 0xC1, 0xF9]]])  # (77,193,249)
        hsv_color = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[0, 0]
        h, s, v = int(hsv_color[0]), int(hsv_color[1]), int(hsv_color[2])

        lower = np.array([max(0, h - 7), max(20, s - 80), max(50, v - 60)])
        upper = np.array([min(180, h + 7), min(255, s + 80), min(255, v + 60)])

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        ratio = np.count_nonzero(mask) / (img.shape[0] * img.shape[1])
        return ratio > min_ratio

    # ---- color-based classifier (rápido) ----
    def _classify_cell(self, cell_img: np.ndarray) -> PointType:
        hsv = cv2.cvtColor(cell_img, cv2.COLOR_BGR2HSV)
        total = cell_img.shape[0] * cell_img.shape[1]

        green_mask = cv2.inRange(hsv, (35, 50, 50), (85, 255, 255))
        red_mask1 = cv2.inRange(hsv, (0, 120, 50), (10, 255, 255))
        red_mask2 = cv2.inRange(hsv, (160, 120, 50), (180, 255, 255))
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        blue_mask = cv2.inRange(hsv, (90, 40, 40), (130, 255, 255))
        white_mask = cv2.inRange(hsv, (0, 0, 200), (180, 70, 255))

        green_ratio = np.count_nonzero(green_mask) / total
        red_ratio = np.count_nonzero(red_mask) / total
        blue_ratio = np.count_nonzero(blue_mask) / total
        white_ratio = np.count_nonzero(white_mask) / total

        if green_ratio > 0.50:
            return PointType.EMPTY
        if red_ratio > 0.04:
            return PointType.FOOD
        if white_ratio > 0.04:
            return PointType.HEAD_U
        if blue_ratio > 0.02:
            return PointType.BODY_VER

        v_mean = hsv[:, :, 2].mean()
        s_mean = hsv[:, :, 1].mean()
        if v_mean > 200 and s_mean < 70:
            return PointType.HEAD_U

        return None

    def _map_grid_from_board(self, board: np.ndarray) -> List[List[PointType]]:
        grid = []
        h_cell = self.cell_size
        w_cell = self.cell_size
        for i in range(self.rows):
            row = []
            y0 = i * h_cell
            y1 = y0 + h_cell
            for j in range(self.cols):
                x0 = j * w_cell
                x1 = x0 + w_cell
                cell = board[y0:y1, x0:x1]
                row.append(self._classify_cell(cell))
            grid.append(row)
        return grid

    def _stabilize_grid(self, new_grid: List[List[PointType]]) -> List[List[PointType]]:
        self._last_grids.append(new_grid)
        frames = list(self._last_grids)
        n = len(frames)
        majority = (n // 2) + 1

        stable = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                vals = [frames[f][i][j] for f in range(n)]
                cnt = Counter(vals)
                most_common, count = cnt.most_common(1)[0]
                if count >= majority:
                    row.append(most_common)
                    continue
                recent_non_empty = None
                for v in reversed(vals):
                    if v not in (PointType.EMPTY, PointType.NONE):
                        recent_non_empty = v
                        break
                if recent_non_empty is not None:
                    row.append(recent_non_empty)
                else:
                    row.append(vals[-1])
            stable.append(row)
        return stable

    # ---- API pública ----
    def get_stable_grid_from_board(self, board: np.ndarray) -> List[List[PointType]]:
        raw = self._map_grid_from_board(board)
        stable = self._stabilize_grid(raw)
        return stable

    def to_grid_string(self, grid: List[List[PointType]]) -> str:
        """Convierte la grilla a una representación de texto simple."""
        mapping = {
            PointType.EMPTY: "E",
            PointType.FOOD: "F",
            PointType.HEAD_U: "H",
            PointType.HEAD_D: "H",
            PointType.HEAD_L: "H",
            PointType.HEAD_R: "H",
            PointType.BODY_VER: "B",
            PointType.BODY_HOR: "B",
            PointType.BODY_DL: "B",
            PointType.BODY_LU: "B",
            PointType.BODY_UR: "B",
            PointType.BODY_RD: "B",
        }
        return "\n".join(
            " ".join(mapping.get(cell, "?") for cell in row) for row in grid
        )


if __name__ == "__main__":
    import time

    scanner = Scanner(region=(100, 100, 595, 525), rows=15, cols=17, cell_size=35)
    scanner.clear_screenshots()

    pyautogui.hotkey("alt", "tab")
    time.sleep(0.6)

    while True:
        board = scanner.capture()
        grid = scanner.get_stable_grid_from_board(board)
        print(scanner.to_grid_string(grid))
        print("=" * 50)
