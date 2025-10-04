import os
from sys import argv
from time import sleep
from typing import List, Tuple

import cv2
import numpy as np
from mss import mss

from base import Pos

ROWS = 15 
COLS = 17

RED_COLOR_RANGES = [([0, 70, 50], [10, 255, 255]), ([170, 70, 50], [179, 255, 255])]


class Scanner:
    def __init__(self, region: Tuple[int, int, int, int]):
        """Region es una tupla (x, y, width, height)"""
        self._x = region[0]
        self._y = region[1]
        self._width = region[2]
        self._height = region[3]
        self._block_size = (self._width // COLS, self._height // ROWS)
        self._sct = mss()  # Se guarda la instacia de mss

    def capture_region(self) -> np.ndarray:
        """
        Hace una captura de pantalla según las regiones dadas en el constructor.
        Regresa:
        np.ndarray: Un arreglo de numpy con la captura en formato BGR.
        """
        monitor = {
            "left": self._x,
            "top": self._y,
            "width": self._width,
            "height": self._height,
        }
        shot = self._sct.grab(monitor)
        img = np.array(shot)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img_bgr

    def save_image(self, file_name: str) -> None:
        """
        Guarda la imagen tomada por capture_region en la carpeta screenshots.
        Parametros:
        file_name (str): Nombre del archivo en screenshots
        """
        folder_name = "screenshots"
        if not os.path.isdir(folder_name):
            os.makedirs(folder_name)
        file_path = os.path.join(folder_name, file_name)

        frame = self.capture_region()
        cv2.imwrite(file_path, frame)
        print(f"Imagen guardada en {file_path}")

    def save_multiple_images(self, delay: int, num: int) -> None:
        """
        Guarda muchas imagenes del juego corriendo en la carpeta screenshots
        Parametros:
        delay (int): Cuantos segundos se demora en tomar la imagen
        num (int): Cuantas imagenes se quieren tomar
        """
        # Clean folder
        folder_name = "screenshots"
        for file_name in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file_name)
            os.remove(file_path)

        n = 0
        while n < num:
            file_name = "frame" + str(n) + ".png"
            self.save_image(file_name)
            n += 1
            sleep(delay)

    def load_image(self, file_path: str) -> np.ndarray:
        """
        Carga una imagen desde el disco y la retorna.
        Parámetros:
        path (str): Path completo de la imagen a cargar.
        Regresa:
        np.ndarray: Imagen cargada en formato BGR.
        """
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen en {file_path}")
        return img

    def get_color_mask(
        self, img_bgr: np.ndarray, color_ranges: List[Tuple]
    ) -> np.ndarray:
        """
        Dada una imagen en BGR regresa una mascara según los rangos del color
        Parametros:
        img_bgr (np.ndarray): Arreglo de numpy que representa una imagen en formato BGR
        color_ranges (List(Tuple)): Una lista con los rangos de color en HSV
        Regresa:
        np.ndarray: Una mascara binaria con solo los puntos donde esta el color
        """
        # Se convierte la imagen de BGR a HSV por simplicidad
        # TODO: Se podria poner la imagen directamente en HSV?
        image_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        img_w, img_h = image_hsv.shape[:2]

        # Se crea una mascara inicial de ceros para filtrar el color
        color_mask = np.zeros((img_w, img_h), dtype=np.uint8)

        # En HSV los colores pueden tener distintos rangos.
        # Para crear una única mascara que detecte ese color hay que combinar los rangos
        for color_range in color_ranges:
            lower, upper = color_range
            temp_mask = cv2.inRange(image_hsv, np.array(lower), np.array(upper))

            # Combina la mascara acual con la temporal
            color_mask = cv2.bitwise_or(color_mask, temp_mask)

        return color_mask

    def ratio_blocks(self, mask: np.ndarray):
        """
        Calcula cual es la proporción del color en la mascara por cada bloque del tablero
        Argumentos:
        (np.ndarray): Mascara de un color en especifico
        Regresa:
        np.ndarray: Arreglo de tamaño (ROWS, COLS) con los promedios del color en cada bloque
        """
        block_w, block_h = self._block_size
        mask_w, mask_h = mask.shape

        # Verificar que la imagen encaja exactemente con la grilla
        assert mask_h == block_h * COLS, (
            f"La altura no coincide {mask_h} != {block_h} * {COLS} == {block_h * COLS}"
        )
        assert mask_w == block_w * ROWS, (
            f"La anchura no coincide {mask_w} != {block_w} * {ROWS} == {block_w * ROWS}"
        )

        # Se subdivide la mascara en bloques de tamaño block_h y block_w
        reshaped = mask.reshape(ROWS, block_h, COLS, block_w, copy=False)

        # Se saca el promedio cuanto color hay en el bloque
        results = reshaped.mean(axis=(1, 3))

        return results

    def apple_coords(self, img_bgr: np.ndarray) -> Pos:
        """
        Calcula las coordenadas de la manzana en base a img_bgr
        Parametros:
        img_bgr (np.ndarray): Un arreglo de numpy que contiene la imagen en formato BGR
        Regresa
        Pos(x,y): Objeto tipo Pos con las coordenadas (x,y) de la manzana
        """
        mask = self.get_color_mask(img_bgr, RED_COLOR_RANGES)
        red_cells = self.ratio_blocks(mask)
        max_index = np.argmax(red_cells)
        location = np.unravel_index(max_index, red_cells.shape)

        print(f"Index: {max_index}")
        # No detecta niguna manzana o lengua
        if max_index <= 0:
            return Pos(0, 0)
        # Detecta manzana o lengua
        elif max_index > 0:
            return Pos(int(location[0]) + 1, int(location[1]) + 1)


def run(screen_corner_x, screen_corner_y, board_size_x, board_size_y):
    screen_region = (
        int(screen_corner_x),
        int(screen_corner_y),
        int(board_size_x),
        int(board_size_y),
    )
    scanner = Scanner(screen_region)

    img_bgr = scanner.load_image("./screenshots/frame13.png")
    print(scanner.apple_coords(img_bgr))


if __name__ == "__main__":
    if len(argv) < 5:
        # Hay que cambiar estas posiciones según su resolución
        # TODO: Hacer un archivo .config con las posicioens en la pantalla de cada uno
        x1, y1 = 411, 237
        x2, y2 = 955, 717
        board_width = x2 - x1
        board_height = y2 - y1
        run(x1, y1, board_width, board_height)
    else:
        run(argv[1], argv[2], argv[3], argv[4])
